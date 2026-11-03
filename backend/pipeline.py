from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select

from backend.gmail.fetch import fetch_tnp_emails
from backend.graph.graph import workflow
from backend.db.database import create_db_and_tables, engine
from backend.db.models import User
from backend.schemas.models import RawEmail
from backend.db.crud import (
    is_duplicate_email,
    save_email,
    save_extraction_result,
    record_failure,
    get_latest_received_at,
    get_stuck_emails,
)
from backend.timeutils import as_utc, to_ist
from backend.notification.push import send_push_notification
from backend.auth.gmail_auth import get_gmail_service

# Only notify about emails that arrived recently. Stops a first sync, or a run
# after the scheduler was down, from sending a burst of old notifications.
NOTIFY_WINDOW = timedelta(hours=1)
PUSH_BODY_MAX_CHARS = 100   # keep lock-screen text short


def notify_if_verified(session, user, extraction_row, email_row):
    if extraction_row.processing_status != "verified":
        return False
    if as_utc(email_row.received_at) < datetime.now(timezone.utc) - NOTIFY_WINDOW:
        return False

    title = extraction_row.company_name or "New TNP Notice"
    if extraction_row.deadline:
        body = f"Deadline: {to_ist(extraction_row.deadline).strftime('%b %d, %I:%M %p')} IST"
    else:
        body = (extraction_row.summary or "")[:PUSH_BODY_MAX_CHARS]
    send_push_notification(session, user.id, title, body)
    return True


def process_email(session, user, email_row, raw_email):
    try:
        result = workflow.invoke({"raw_email": raw_email})
    except Exception as e:
        failure = record_failure(session, email_row.id)
        print(f"Failed ({failure.retry_count}): {raw_email.subject} -> {e}")
        return

    extraction_row = save_extraction_result(session, email_row.id, result)
    print(f"Saved: {raw_email.subject} -> status={extraction_row.processing_status}")
    try:
        notify_if_verified(session, user, extraction_row, email_row)
    except Exception as e:
        print(f"Notify failed for {raw_email.subject}: {e}")


def process_user(session, user):
    service = get_gmail_service(user.email)

    # Pass 1: saved emails whose processing crashed or never finished. Runs first so
    # an email that fails in pass 2 is not retried again in the same run.
    for email_row in get_stuck_emails(session, user_id=user.id):
        raw_email = RawEmail(
            gmail_message_id=email_row.gmail_message_id,
            subject=email_row.subject or "",
            body=email_row.body or "",
            received_at=as_utc(email_row.received_at),
        )
        print(f"Retrying stuck email: {raw_email.subject}")
        process_email(session, user, email_row, raw_email)

    # Pass 2: new emails since the newest one we have saved (the bookmark).
    latest = get_latest_received_at(session, user_id=user.id)
    for raw_email in fetch_tnp_emails(service, after=latest):
        if is_duplicate_email(session, raw_email.gmail_message_id):
            continue
        email_row = save_email(session, raw_email, user_id=user.id)
        process_email(session, user, email_row, raw_email)


def run_pipeline():
    create_db_and_tables()

    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            # One user's failure (revoked token, Gmail outage) must not stop the others.
            try:
                process_user(session, user)
            except Exception as e:
                session.rollback()
                print(f"Skipping {user.email}: {e}")
