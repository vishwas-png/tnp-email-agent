from fastapi import FastAPI, Depends
from sqlmodel import Session
from backend.db.database import get_session
from backend.db.crud import get_verified_notices,to_ist
from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from backend.auth.gmail_auth import SCOPES, CREDENTIALS_FILE
from backend.db.models import User,PushSubscriptionDB
from sqlmodel import select
from backend.auth.encrypt import encrypt_token , decrypt_token
from fastapi.middleware.cors import CORSMiddleware
from backend.auth.jwt_handler import create_access_token,create_refresh_token,verify_token
from fastapi import Response
from fastapi import Cookie
from fastapi import HTTPException


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)
from pydantic import BaseModel

class SubscriptionData(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


@app.get("/notices")
def read_notices(access_token: str = Cookie(None),session: Session = Depends(get_session)):

    if access_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    payload = verify_token(access_token)
    user_email = payload["sub"]
    user = session.exec(select(User).where(User.email == user_email)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    results = get_verified_notices(session,user.id)

    notices = []
    for email, extraction in results:
        notice_dict=({
            "gmail_message_id":email.gmail_message_id,
            "subject": email.subject,
            "received_at": to_ist(email.received_at),
            "summary": extraction.summary,
            "action_items": extraction.action_items,
        })
        if extraction.category:
          notice_dict["category"] = extraction.category
        if extraction.deadline:
          notice_dict["deadline"]=to_ist(extraction.deadline)

        if extraction.company_name:
           notice_dict["company_name"]=extraction.company_name

        notices.append(notice_dict)


    return notices

REDIRECT_URI = "http://localhost:8000/oauth/callback"
@app.get("/connect-gmail")
def connect_gmail(email:str):
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
        , autogenerate_code_verifier=False
    )
    authorization_url,state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=email
    )
    return RedirectResponse(authorization_url)

@app.get("/oauth/callback")
def callback(code:str,state:str,response: Response,session:Session = Depends(get_session)):
      flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            autogenerate_code_verifier=False
       )
      flow.fetch_token(         
           code=code
           )

      creds=flow.credentials
      user = session.exec(select(User).where(User.email == state)).first()
      if user is None:
        return {"error": f"No user found for email {state}"}

      user.token_json = encrypt_token(creds.to_json())
      session.add(user)
      session.commit()


      access_token = create_access_token(state)
      refresh_token = create_refresh_token(state)
      response.set_cookie(key="access_token", value=access_token, httponly=True)
      response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)   

      return {"status": "success", "email": state}


@app.get("/refresh-token")
def refresh_token_route(response: Response, refresh_token: str = Cookie(None)):
   if refresh_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")
   payload = verify_token(refresh_token)
   user_email = payload["sub"]

   new_access_token = create_access_token(user_email)
   response.set_cookie(key="access_token", value=new_access_token, httponly=True)

   return { "status":"refreshed"}

@app.post("/save-subscription")
def save_subscription(
    data: SubscriptionData,
    access_token: str = Cookie(None),
    session: Session = Depends(get_session)
):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    payload = verify_token(access_token)
    user_email = payload["sub"]

    user = session.exec(select(User).where(User.email == user_email)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    subscription = PushSubscriptionDB(
        user_id=user.id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth
    )
    session.add(subscription)
    session.commit()

    return {"status": "subscription saved"}
      