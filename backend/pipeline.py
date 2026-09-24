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
from datetime import datetime, timezone, timedelta
from backend.notification.push import send_push_notification
from sqlmodel import select
from backend.db.models import User, Email
from backend.auth.gmail_auth import get_gmail_service

def notify_if_verified(session, user, extraction_row, subject, received_at):
    print(f"Saved: {subject} -> status={extraction_row.processing_status}")
    if extraction_row.processing_status == "verified":
        is_recent = received_at > datetime.now(timezone.utc) - timedelta(hours=1)
        if is_recent:
            title = extraction_row.company_name if extraction_row.company_name else "New TNP Notice"
            if extraction_row.deadline:
                body = f"Deadline: {extraction_row.deadline.strftime('%b %d, %I:%M %p')}"
            else:
                body = extraction_row.summary
            send_push_notification(session, user.id, title, body)

def run_pipeline():
    create_db_and_tables()

    with next(get_session()) as session:
        users = session.exec(select(User)).all()

        for user in users:
            try:
                service = get_gmail_service(user.email)
            except ValueError as e:
                print(f"Skipping {user.email}: {e}")
                continue

            latest = get_latest_received_at(session, user_id=user.id)
            new_emails = fetch_tnp_emails(service, after=latest)

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
                notify_if_verified(session, user, extraction_row, raw_email.subject,email_row.received_at)
                
            stuck = get_stuck_emails(session, user_id=user.id)
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
                notify_if_verified(session, user, extraction_row, raw_email.subject,email_row.received_at)
                