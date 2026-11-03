import os
import secrets
from fastapi import FastAPI, Depends, Response, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.db.database import get_session
from backend.db.crud import get_verified_notices, get_or_create_user, to_ist
from backend.db.models import User, PushSubscriptionDB
from backend.auth.gmail_auth import SCOPES, CREDENTIALS_FILE, get_account_email
from backend.auth.encrypt import encrypt_token
from backend.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

REDIRECT_URI = "http://localhost:8000/oauth/callback"

# Secure cookies are only sent over HTTPS, so this is off for localhost and on in production.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_LIFETIME_SECONDS = 600


def set_cookie(response: Response, key: str, value: str, max_age: int):
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path="/",
        httponly=True,       # JavaScript cannot read it, so XSS cannot steal it
        secure=COOKIE_SECURE,
        samesite="lax",      # not sent on cross-site POSTs, which blocks CSRF on our POST routes
    )


def set_auth_cookies(response: Response, email: str):
    set_cookie(response, "access_token", create_access_token(email), int(ACCESS_TOKEN_LIFETIME.total_seconds()))
    set_cookie(response, "refresh_token", create_refresh_token(email), int(REFRESH_TOKEN_LIFETIME.total_seconds()))


def get_current_user(access_token: str = Cookie(None), session: Session = Depends(get_session)) -> User:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    payload = verify_token(access_token, expected_type="access")
    user = session.exec(select(User).where(User.email == payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def make_flow():
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=False
    )


class SubscriptionData(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


@app.get("/notices")
def read_notices(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    results = get_verified_notices(session, user.id)

    notices = []
    for email, extraction in results:
        notice_dict = {
            "gmail_message_id": email.gmail_message_id,
            "subject": email.subject,
            "received_at": to_ist(email.received_at),
            "summary": extraction.summary,
            "action_items": extraction.action_items,
        }
        if extraction.category:
            notice_dict["category"] = extraction.category
        if extraction.deadline:
            notice_dict["deadline"] = to_ist(extraction.deadline)
        if extraction.company_name:
            notice_dict["company_name"] = extraction.company_name

        notices.append(notice_dict)

    return notices


@app.get("/connect-gmail")
def connect_gmail():
    # state is a random one-time value. Google sends it back, and the callback checks
    # it matches this cookie, so an attacker cannot start a login for someone else.
    state = secrets.token_urlsafe(32)
    authorization_url, _ = make_flow().authorization_url(
        access_type='offline',
        prompt='consent',
        state=state
    )
    response = RedirectResponse(authorization_url)
    set_cookie(response, OAUTH_STATE_COOKIE, state, OAUTH_STATE_LIFETIME_SECONDS)
    return response


@app.get("/oauth/callback")
def callback(
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: str | None = Cookie(None),
    session: Session = Depends(get_session),
):
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")

    if error:
        raise HTTPException(status_code=400, detail=f"Google login failed: {error}")
    if not code or not state or not oauth_state or not secrets.compare_digest(state, oauth_state):
        raise HTTPException(status_code=400, detail="Invalid login state, please start again")

    flow = make_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Identity comes from Google: whoever owns this token is who logs in.
    email = get_account_email(creds)
    user = get_or_create_user(session, email)
    user.token_json = encrypt_token(creds.to_json())
    session.add(user)
    session.commit()

    set_auth_cookies(response, email)
    return {"status": "success", "email": email}


@app.post("/refresh-token")
def refresh_token_route(response: Response, refresh_token: str = Cookie(None)):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    payload = verify_token(refresh_token, expected_type="refresh")

    set_cookie(response, "access_token", create_access_token(payload["sub"]), int(ACCESS_TOKEN_LIFETIME.total_seconds()))
    return {"status": "refreshed"}


@app.post("/save-subscription")
def save_subscription(
    data: SubscriptionData,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    subscription = PushSubscriptionDB(
        user_id=user.id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth
    )
    session.add(subscription)
    session.commit()

    return {"status": "subscription saved"}
