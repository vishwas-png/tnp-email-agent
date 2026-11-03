import base64
from backend.gmail import fetch
from backend.gmail.fetch import strip_quoted_reply, fetch_tnp_emails


def b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode()


def message(msg_id, day, body="Hello", mime="text/plain", date=None):
    return {
        "id": msg_id,
        "payload": {
            "mimeType": mime,
            "headers": [
                {"name": "Subject", "value": f"Notice {msg_id}"},
                {"name": "Date", "value": date or f"Mon, {day:02d} Oct 2026 10:00:00 +0530"},
            ],
            "body": {"data": b64(body)},
        },
    }


class Exec:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeGmail:
    """Mimics service.users().messages().list/get. Messages are stored newest first, like Gmail."""

    def __init__(self, messages, page_size=2):
        self.messages_by_id = {m["id"]: m for m in messages}
        self.order = [m["id"] for m in messages]
        self.page_size = page_size
        self.queries = []

    def users(self):
        return self

    def messages(self):
        return self

    def list(self, userId, q, pageToken=None, maxResults=None):
        self.queries.append(q)
        start = int(pageToken or 0)
        page = self.order[start:start + self.page_size]
        response = {"messages": [{"id": i} for i in page]}
        if start + self.page_size < len(self.order):
            response["nextPageToken"] = str(start + self.page_size)
        return Exec(response)

    def get(self, userId, id, format):
        return Exec(self.messages_by_id[id])


def test_strip_keeps_sentences_that_start_with_on():
    body = "Dear students,\nOn Friday the OA moves to the Computer Centre.\nBring your ID.\n"
    assert strip_quoted_reply(body) == body


def test_strip_cuts_at_reply_header():
    body = "Venue changed.\n\nOn Mon, 5 Oct 2026 at 10:00, TNP Cell <tnp@x.in> wrote:\n> old text"
    assert strip_quoted_reply(body) == "Venue changed.\n\n"


def test_strip_handles_header_wrapped_onto_two_lines():
    body = "Venue changed.\nOn Mon, 5 Oct 2026 at 10:00, TNP Cell\n<tnp@x.in> wrote:\n> old text"
    assert strip_quoted_reply(body) == "Venue changed.\n"


def test_fetch_follows_all_pages_and_returns_oldest_first():
    gmail = FakeGmail([message(f"m{d}", d) for d in (5, 4, 3, 2, 1)], page_size=2)
    emails = fetch_tnp_emails(gmail)
    assert [e.gmail_message_id for e in emails] == ["m1", "m2", "m3", "m4", "m5"]


def test_fetch_cap_keeps_the_oldest_so_the_bookmark_skips_nothing(monkeypatch):
    monkeypatch.setattr(fetch, "MAX_EMAILS_PER_RUN", 2)
    gmail = FakeGmail([message(f"m{d}", d) for d in (5, 4, 3, 2, 1)])
    assert [e.gmail_message_id for e in fetch_tnp_emails(gmail)] == ["m1", "m2"]


def test_query_uses_initial_window_then_bookmark():
    from datetime import datetime, timezone
    bookmark = datetime(2026, 10, 1, tzinfo=timezone.utc)
    gmail = FakeGmail([])
    fetch_tnp_emails(gmail)
    fetch_tnp_emails(gmail, after=bookmark)
    assert "newer_than:30d" in gmail.queries[0]
    assert f"after:{int(bookmark.timestamp())}" in gmail.queries[1]


def test_single_part_html_is_stripped_to_text():
    gmail = FakeGmail([message("m1", 1, body="<p>Apply <b>now</b></p>", mime="text/html")])
    assert fetch_tnp_emails(gmail)[0].body == "Apply now"


def test_minus_zero_date_becomes_timezone_aware():
    gmail = FakeGmail([
        message("m1", 1, date="Mon, 01 Oct 2026 10:00:00 -0000"),
        message("m2", 2),
    ])
    emails = fetch_tnp_emails(gmail)
    assert all(e.received_at.tzinfo is not None for e in emails)
