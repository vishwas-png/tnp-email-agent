from fastapi import FastAPI, Depends
from sqlmodel import Session
from backend.db.database import get_session
from backend.db.crud import get_verified_notices,to_ist
from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from backend.auth.gmail_auth import SCOPES, CREDENTIALS_FILE
from backend.db.models import User
from sqlmodel import select
from backend.auth.encrypt import encrypt_token , decrypt_token
app = FastAPI()

@app.get("/notices")
def read_notices(session: Session = Depends(get_session)):
    results = get_verified_notices(session)

    notices = []
    for email, extraction in results:
        notices.append({
            "subject": email.subject,
            "received_at": to_ist(email.received_at),
            "company_name": extraction.company_name,
            "deadline": to_ist(extraction.deadline),
            "summary": extraction.summary,
            "action_items": extraction.action_items,
        })

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
def callback(code:str,state:str,session:Session = Depends(get_session)):
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

      return {"status": "success", "email": state}