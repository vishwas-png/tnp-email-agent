from datetime import datetime, timedelta, timezone
from sqlmodel import select
import pytest

from backend import pipeline
from backend.db.crud import save_email, save_extraction_result, MAX_PIPELINE_ATTEMPTS
from backend.db.models import ExtractedInfoDB, Email
from backend.schemas.models import RawEmail, ExtractedInfo, EmailCategory
from tests.conftest import make_user

IST = timezone(timedelta(hours=5, minutes=30))


def raw(msg_id, received_at):
    return RawEmail(gmail_message_id=msg_id, subject=f"Subject {msg_id}", body="body", received_at=received_at)


def verified_result(deadline=None):
    info = ExtractedInfo(category=EmailCategory.PLACEMENT, summary="Apply soon", company_name="Acme", deadline=deadline)
    return {"extracted_info": info, "processing_status": "verified", "retry_count": 0}


@pytest.fixture
def pushes(monkeypatch):
    sent = []
    monkeypatch.setattr(pipeline, "send_push_notification",
                        lambda session, user_id, title, body: sent.append((user_id, title, body)))
    return sent


def save_verified(session, user, received_at, deadline=None):
    # Round-trips through SQLite, so received_at comes back naive (the original crash).
    email_row = save_email(session, raw("m1", received_at), user_id=user.id)
    session.refresh(email_row)
    return email_row, save_extraction_result(session, email_row.id, verified_result(deadline))


def test_recent_verified_email_notifies(session, user, pushes):
    email_row, extraction = save_verified(session, user, datetime.now(timezone.utc) - timedelta(minutes=5))
    assert email_row.received_at.tzinfo is None
    assert pipeline.notify_if_verified(session, user, extraction, email_row) is True
    assert pushes == [(user.id, "Acme", "Apply soon")]


def test_old_email_does_not_notify(session, user, pushes):
    email_row, extraction = save_verified(session, user, datetime.now(timezone.utc) - timedelta(hours=2))
    assert pipeline.notify_if_verified(session, user, extraction, email_row) is False
    assert pushes == []


def test_push_deadline_is_shown_in_ist(session, user, pushes):
    deadline = datetime(2026, 11, 2, 23, 59, tzinfo=IST)
    email_row, extraction = save_verified(session, user, datetime.now(timezone.utc), deadline=deadline)
    pipeline.notify_if_verified(session, user, extraction, email_row)
    assert pushes[0][2] == "Deadline: Nov 02, 11:59 PM IST"


class FakeWorkflow:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = 0

    def invoke(self, state):
        self.calls += 1
        if self.fail:
            raise RuntimeError("LLM returned bad JSON")
        return verified_result()


@pytest.fixture
def wired(engine, monkeypatch, pushes):
    """Point run_pipeline at the test DB, with Gmail and the LLM replaced."""
    monkeypatch.setattr(pipeline, "engine", engine)
    monkeypatch.setattr(pipeline, "create_db_and_tables", lambda: None)
    monkeypatch.setattr(pipeline, "get_gmail_service", lambda email: email)
    inbox = {}
    monkeypatch.setattr(pipeline, "fetch_tnp_emails", lambda service, after=None: inbox.get(service, []))
    return inbox


def test_one_broken_user_does_not_stop_the_others(session, wired, monkeypatch):
    make_user(session, "broken@example.com")
    good = make_user(session, "good@example.com")
    wired["good@example.com"] = [raw("g1", datetime.now(timezone.utc))]

    def gmail(email):
        if email == "broken@example.com":
            raise RuntimeError("token revoked")
        return email

    monkeypatch.setattr(pipeline, "get_gmail_service", gmail)
    monkeypatch.setattr(pipeline, "workflow", FakeWorkflow())
    pipeline.run_pipeline()

    saved = session.exec(select(Email)).all()
    assert [(e.gmail_message_id, e.user_id) for e in saved] == [("g1", good.id)]


def test_failing_email_is_retried_then_given_up(session, user, wired, monkeypatch):
    wired[user.email] = [raw("m1", datetime.now(timezone.utc))]
    flow = FakeWorkflow(fail=True)
    monkeypatch.setattr(pipeline, "workflow", flow)

    for _ in range(MAX_PIPELINE_ATTEMPTS + 2):
        pipeline.run_pipeline()

    rows = session.exec(select(ExtractedInfoDB)).all()
    assert len(rows) == 1
    assert rows[0].processing_status == "failed_error"
    assert flow.calls == MAX_PIPELINE_ATTEMPTS


def test_stuck_email_recovers_into_a_single_row(session, user, wired, monkeypatch, pushes):
    wired[user.email] = [raw("m1", datetime.now(timezone.utc))]
    monkeypatch.setattr(pipeline, "workflow", FakeWorkflow(fail=True))
    pipeline.run_pipeline()

    monkeypatch.setattr(pipeline, "workflow", FakeWorkflow())
    pipeline.run_pipeline()

    rows = session.exec(select(ExtractedInfoDB)).all()
    assert [r.processing_status for r in rows] == ["verified"]
    assert len(pushes) == 1
