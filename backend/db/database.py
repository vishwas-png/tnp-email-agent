import os
from sqlmodel import SQLModel, create_engine, Session
from backend.db.models import User, Email, ExtractedInfoDB

DATABASE_URL = "sqlite:///./tnp_agent.db"

# echo=True printed every SQL statement with its values (email bodies, encrypted tokens).
engine = create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO") == "1")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session