import json
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from backend.api import main
from backend.auth.jwt_handler import create_access_token
from backend.db.database import get_session
from backend.db.models import Email, ExtractedInfoDB
from tests.conftest import make_user

NOW = datetime.now(timezone.utc)


def add_notice(session, user, msg_id, received_days_ago=0, deadline_in_days=None,
               category="placement", company="Acme", status="verified", summary="A notice"):
    email = Email(gmail_message_id=msg_id, user_id=user.id, subject=f"Subject {msg_id}", body="b",
                  received_at=NOW - timedelta(days=received_days_ago))
    session.add(email)
    session.commit()
    session.refresh(email)
    session.add(ExtractedInfoDB(
        email_id=email.id, category=category, company_name=company, summary=summary,
        deadline=NOW + timedelta(days=deadline_in_days) if deadline_in_days is not None else None,
        action_items=json.dumps(["Apply via form"]), processing_status=status,
    ))
    session.commit()


@pytest.fixture
def client(session, user):
    main.app.dependency_overrides[get_session] = lambda: session
    c = TestClient(main.app)
    c.cookies.set("access_token", create_access_token(user.email))
    yield c
    main.app.dependency_overrides.clear()


def ids(response):
    return [n["gmail_message_id"] for n in response.json()["items"]]


def test_newest_first_with_paging(client, session, user):
    for day in range(5):
        add_notice(session, user, f"m{day}", received_days_ago=day)

    first = client.get("/notices", params={"limit": 2})
    assert ids(first) == ["m0", "m1"] and first.json()["has_more"] is True

    last = client.get("/notices", params={"limit": 2, "offset": 4})
    assert ids(last) == ["m4"] and last.json()["has_more"] is False


def test_only_verified_notices_of_this_user(client, session, user):
    other = make_user(session, "other@example.com")
    add_notice(session, user, "mine")
    add_notice(session, user, "failed", status="failed_validation")
    add_notice(session, other, "theirs")
    assert ids(client.get("/notices")) == ["mine"]


def test_category_filter_and_search(client, session, user):
    add_notice(session, user, "p1", category="placement", company="Acme")
    add_notice(session, user, "i1", category="internship", company="Globex")
    add_notice(session, user, "i2", category="internship", company="Initech", summary="Data science role")

    assert sorted(ids(client.get("/notices", params={"category": "internship"}))) == ["i1", "i2"]
    assert ids(client.get("/notices", params={"q": "globex"})) == ["i1"]          # company, any case
    assert ids(client.get("/notices", params={"q": "data science"})) == ["i2"]    # summary
    assert client.get("/notices", params={"category": "nonsense"}).status_code == 422


def test_deadline_sort_puts_soonest_upcoming_first(client, session, user):
    add_notice(session, user, "later", received_days_ago=3, deadline_in_days=10)
    add_notice(session, user, "soon", received_days_ago=2, deadline_in_days=1)
    add_notice(session, user, "passed", received_days_ago=0, deadline_in_days=-1)
    add_notice(session, user, "none", received_days_ago=1)

    order = ids(client.get("/notices", params={"sort": "deadline"}))
    assert order[:2] == ["soon", "later"]
    assert order[2:] == ["passed", "none"]  # the rest, newest first


def test_notice_fields(client, session, user):
    add_notice(session, user, "m1", deadline_in_days=2)
    notice = client.get("/notices").json()["items"][0]
    assert notice["action_items"] == ["Apply via form"]
    assert notice["deadline"].endswith("+05:30")  # shown in IST
    assert {"role", "apply_link", "eligibility", "company_name"} <= notice.keys()


def test_stats(client, session, user):
    add_notice(session, user, "new_with_deadline", received_days_ago=1, deadline_in_days=3)
    add_notice(session, user, "old_far_deadline", received_days_ago=20, deadline_in_days=30)
    add_notice(session, user, "old_passed", received_days_ago=20, deadline_in_days=-2)
    add_notice(session, make_user(session, "other@example.com"), "theirs", deadline_in_days=1)

    assert client.get("/stats").json() == {"total": 3, "new_this_week": 1, "deadlines_next_7_days": 1}
