import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

load_dotenv()
JWT_KEY = os.getenv("JWT_SECRET")

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=30)


def _create_token(email, token_type, lifetime):
    payload = {
        "sub": email,
        # Both tokens share one key, so the type claim stops a 30-day refresh
        # token from being used as an access token.
        "type": token_type,
        "exp": datetime.now(timezone.utc) + lifetime,
    }
    return jwt.encode(payload, JWT_KEY, algorithm="HS256")


def create_access_token(email):
    return _create_token(email, "access", ACCESS_TOKEN_LIFETIME)


def create_refresh_token(email):
    return _create_token(email, "refresh", REFRESH_TOKEN_LIFETIME)


def verify_token(token, expected_type="access"):
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload
