import jwt
import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import HTTPException
JWT_KEY=os.getenv("JWT_SECRET");


from datetime import datetime, timedelta, timezone



def create_access_token(email):
    payload = {
        "sub": email,
        "exp":datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    access_token = jwt.encode(payload, JWT_KEY, algorithm="HS256")
    return access_token

def create_refresh_token(email):
    payload={
        "sub":email,
        "exp":datetime.now(timezone.utc) + timedelta(days=30)
    }
    refresh_token=jwt.encode(payload,JWT_KEY,algorithm="HS256")
    return refresh_token


def verify_token(access_token):
    try:
     payload = jwt.decode(access_token, JWT_KEY, algorithms=["HS256"])
     return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")