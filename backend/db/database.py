from sqlmodel import SQLModel, create_engine, Session
from backend.db.models import User, Email, ExtractedInfoDB

DATABASE_URL = "sqlite:///./tnp_agent.db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session