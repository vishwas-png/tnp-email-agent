from sqlmodel import select

from backend.gmail.fetch import fetch_tnp_emails
from backend.graph.graph import workflow
from backend.db.database import create_db_and_tables, get_session
from backend.db.models import Email
from backend.schemas.models import RawEmail
from backend.db.crud import (
    get_or_create_user,
    needs_processing,
    save_email,
    save_extraction_result,
    get_latest_received_at,
    get_stuck_emails
)


def run_pipeline():
    create_db_and_tables()

    with next(get_session()) as session:
        user = get_or_create_user(session, email="vishwas.sharma.ug23@nsut.ac.in", name="vissuDon")

        latest = get_latest_received_at(session)
        new_emails = fetch_tnp_emails(after=latest)

        for raw_email in new_emails:
            existing = session.exec(
                select(Email).where(Email.gmail_message_id == raw_email.gmail_message_id)
            ).first()
            if existing:
                continue

            email_row = save_email(session, raw_email, user_id=user.id)
            try:
                result = workflow.invoke({"raw_email": raw_email})
            except Exception as e:
                print(f"Failed: {raw_email.subject} -> {e}")
                continue
            extraction_row = save_extraction_result(session, email_row.id, result)
            print(f"Saved: {raw_email.subject} -> status={extraction_row.processing_status}")

        stuck = get_stuck_emails(session)
        for email_row in stuck:
            raw_email = RawEmail(
                gmail_message_id=email_row.gmail_message_id,
                subject=email_row.subject,
                body=email_row.body,
                received_at=email_row.received_at,
            )
            print(f"Retrying stuck email: {raw_email.subject}")
            try:
                result = workflow.invoke({"raw_email": raw_email})
            except Exception as e:
                print(f"Failed again: {raw_email.subject} -> {e}")
                continue
            extraction_row = save_extraction_result(session, email_row.id, result)
            print(f"Saved: {raw_email.subject} -> status={extraction_row.processing_status}")