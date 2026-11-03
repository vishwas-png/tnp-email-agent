import os
from cryptography.fernet import Fernet

# Fake keys, set before any backend import. load_dotenv() never overrides
# variables that already exist, so the real .env is not used by tests.
os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
os.environ["JWT_SECRET"] = "test-jwt-secret-that-is-at-least-32-bytes"
os.environ["GROQ_API_KEY"] = "test-groq-key"

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from backend.db.models import User


@pytest.fixture
def engine():
    # In-memory SQLite shared across connections; the real tnp_agent.db is never touched.
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def make_user(session, email):
    user = User(email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user(session):
    return make_user(session, "student@example.com")
