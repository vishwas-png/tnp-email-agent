from sqlmodel import Session, select, func
from backend.db.models import User, Email, ExtractedInfoDB
import json
from datetime import datetime
from backend.timeutils import as_utc, to_ist  # to_ist is re-exported for the API

# Statuses that end processing. Anything else (no row, or "error") is retried.
TERMINAL_STATUSES = ["verified", "failed_validation", "failed_error"]
MAX_PIPELINE_ATTEMPTS = 3


def get_or_create_user(session: Session, email: str, name: str = None) -> User:
    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    if existing_user:
        return existing_user

    user = User(email=email, name=name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def is_duplicate_email(session: Session, gmail_message_id: str) -> bool:
    statement = select(Email).where(Email.gmail_message_id == gmail_message_id)
    return session.exec(statement).first() is not None


def save_email(session: Session, raw_email, user_id: int) -> Email:
    email_row = Email(
        gmail_message_id=raw_email.gmail_message_id,
        user_id=user_id,
        subject=raw_email.subject,
        body=raw_email.body,
        received_at=as_utc(raw_email.received_at),
    )
    session.add(email_row)
    session.commit()
    session.refresh(email_row)
    return email_row


def get_extraction(session: Session, email_id: int) -> ExtractedInfoDB | None:
    statement = select(ExtractedInfoDB).where(ExtractedInfoDB.email_id == email_id)
    return session.exec(statement).first()


def save_extraction_result(session: Session, email_id: int, result: dict) -> ExtractedInfoDB:
    info = result["extracted_info"]

    # Reuse the row left by an earlier failed attempt, so each email has one row.
    extraction_row = get_extraction(session, email_id) or ExtractedInfoDB(email_id=email_id)
    extraction_row.category = info.category.value if info.category else None
    extraction_row.deadline = as_utc(info.deadline)
    extraction_row.company_name = info.company_name
    extraction_row.role = info.job_role
    extraction_row.eligibility = info.eligibility
    extraction_row.apply_link = info.apply_link
    extraction_row.summary = info.summary
    extraction_row.action_items = json.dumps(info.action_items) if info.action_items else None
    extraction_row.confidence_score = info.confidence_score
    extraction_row.processing_status = result.get("processing_status")
    extraction_row.retry_count = result.get("retry_count", 0)

    session.add(extraction_row)
    session.commit()
    session.refresh(extraction_row)
    return extraction_row


def record_failure(session: Session, email_id: int) -> ExtractedInfoDB:
    # The pipeline raised (LLM error, bad JSON, ...). Count the attempt and give up
    # after MAX_PIPELINE_ATTEMPTS, so a broken email is not retried every 5 minutes forever.
    extraction_row = get_extraction(session, email_id) or ExtractedInfoDB(email_id=email_id, retry_count=0)
    extraction_row.retry_count += 1
    if extraction_row.retry_count >= MAX_PIPELINE_ATTEMPTS:
        extraction_row.processing_status = "failed_error"
    else:
        extraction_row.processing_status = "error"

    session.add(extraction_row)
    session.commit()
    session.refresh(extraction_row)
    return extraction_row


def get_verified_notices(session: Session,user_id:int):
    statement = (
        select(Email, ExtractedInfoDB)
        .join(ExtractedInfoDB, ExtractedInfoDB.email_id == Email.id)
        .where(ExtractedInfoDB.processing_status == "verified")
        .where(Email.user_id == user_id)
        .order_by(Email.received_at.desc())
        .limit(10)
    )
    results = session.exec(statement).all()
    return results


def get_latest_received_at(session: Session, user_id: int) -> datetime | None:
    statement = select(func.max(Email.received_at)).where(Email.user_id == user_id)
    result = session.exec(statement).first()
    return as_utc(result)


def get_stuck_emails(session: Session, user_id: int) -> list[Email]:
    statement = (
        select(Email)
        .outerjoin(ExtractedInfoDB, Email.id == ExtractedInfoDB.email_id)
        .where(
            Email.user_id == user_id,
            (ExtractedInfoDB.id == None) |
            (~ExtractedInfoDB.processing_status.in_(TERMINAL_STATUSES))
        )
        .order_by(Email.received_at)
    )
    return session.exec(statement).all()
