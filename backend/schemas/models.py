from pydantic import BaseModel,Field
from enum import Enum
from datetime import datetime
from uuid import UUID
class JobCategory(str,Enum):
    TECH="tech"
    NON_TECH="non_tech"
    CORE="core"

class EmailCategory(str, Enum):
    GENERAL_NOTICE = "general_notice"
    PLACEMENT = "placement"
    INTERNSHIP = "internship"

class RawEmail(BaseModel):
    gmail_message_id: str
    subject: str
    body: str
    received_at: datetime

class ExtractedInfo(BaseModel):
    category: EmailCategory
    job_category:JobCategory|None = None
    summary: str
    company_name:str|None=None
    job_role:str|None=None
    deadline: datetime | None = None
    eligibility: str | None = None
    action_items: list[str] = []
    apply_link:str|None = None
    confidence_score: float | None = None
    received_at: datetime | None = None

class GraphState(BaseModel):
    raw_email: RawEmail
    category: EmailCategory | None = None
    extracted_info: ExtractedInfo | None = None
    validation_passed: bool = False
    retry_count: int = 0
    processing_status: str | None = None

class NotificationPayload(BaseModel):
    notification_id: UUID
    category: EmailCategory
    summary: str
    deadline: datetime | None = None
    is_read: bool = False