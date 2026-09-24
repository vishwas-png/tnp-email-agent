from sqlmodel import SQLModel , Field
from typing import Optional
from datetime import datetime , timezone


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    name: Optional[str] = None
    token_json:Optional[str] =None

class Email(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    gmail_message_id: str = Field(unique=True)
    user_id: int = Field(foreign_key="user.id")
    subject: Optional[str] = None
    body: Optional[str] = None
    received_at: datetime

class ExtractedInfoDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: int = Field(foreign_key="email.id")
    category: Optional[str] = None
    deadline: Optional[datetime] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    eligibility: Optional[str] = None
    apply_link: Optional[str] = None
    summary: Optional[str] = None
    action_items: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_status: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PushSubscriptionDB(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id:int = Field(foreign_key="user.id")
    ##subscription fields
    endpoint:str
    p256dh:str
    auth:str
