import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlmodel import Session, select
from backend.db.database import engine
from backend.db.models import User
from backend.auth.encrypt import encrypt_token , decrypt_token

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'

def get_gmail_service(user_email: str):
    with Session(engine) as session:
        statement = select(User).where(User.email == user_email)
        user = session.exec(statement).first()

        if user is None or user.token_json is None:
            raise ValueError(f"No token found for user {user_email}")

        token_info = json.loads(decrypt_token(user.token_json))
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            user.token_json = encrypt_token(creds.to_json())
            session.add(user)
            session.commit()

        if not creds or not creds.valid:
            raise ValueError(f"Invalid credentials for user {user_email}, needs re-consent")

        return build('gmail', 'v1', credentials=creds)