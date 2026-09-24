from sqlmodel import Session, select, func
from backend.db.models import User, Email, ExtractedInfoDB
import json
from datetime import timezone, timedelta, datetime

IST = timezone(timedelta(hours=5, minutes=30))

def to_ist(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).astimezone(IST)

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
    received_at_utc = raw_email.received_at.astimezone(timezone.utc)
    email_row = Email(
        gmail_message_id=raw_email.gmail_message_id,
        user_id=user_id,
        subject=raw_email.subject,
        body=raw_email.body,
        received_at=received_at_utc,
    )
    session.add(email_row)
    session.commit()
    session.refresh(email_row)
    return email_row


def save_extraction_result(session: Session, email_id: int, result: dict) -> ExtractedInfoDB:
    info = result["extracted_info"]

    action_items_json = json.dumps(info.action_items) if info.action_items else None

    deadline_utc = info.deadline.astimezone(timezone.utc) if info.deadline else None

    extraction_row = ExtractedInfoDB(
        email_id=email_id,
        category=info.category.value if info.category else None,
        deadline=deadline_utc,
        company_name=info.company_name,
        role=info.job_role,
        eligibility=info.eligibility,
        apply_link=info.apply_link,
        summary=info.summary,
        action_items=action_items_json,
        confidence_score=info.confidence_score,
        processing_status=result.get("processing_status"),
        retry_count=result.get("retry_count", 0),
    )
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


def needs_processing(session: Session, gmail_message_id: str) -> bool:
    email_statement = select(Email).where(Email.gmail_message_id == gmail_message_id)
    existing_email = session.exec(email_statement).first()

    if existing_email is None:
        return True

    extraction_statement = select(ExtractedInfoDB).where(
        ExtractedInfoDB.email_id == existing_email.id,
        ExtractedInfoDB.processing_status.in_(["verified", "failed_validation"])
    )
    completed_extraction = session.exec(extraction_statement).first()

    return completed_extraction is None


def get_latest_received_at(session: Session, user_id: int) -> datetime | None:
    statement = select(func.max(Email.received_at)).where(Email.user_id == user_id)
    result = session.exec(statement).first()
    return result


def get_stuck_emails(session: Session, user_id: int) -> list[Email]:
    statement = (
        select(Email)
        .outerjoin(ExtractedInfoDB, Email.id == ExtractedInfoDB.email_id)
        .where(
            Email.user_id == user_id,
            (ExtractedInfoDB.id == None) |
            (~ExtractedInfoDB.processing_status.in_(["verified", "failed_validation"]))
        )
    )
    return session.exec(statement).all()