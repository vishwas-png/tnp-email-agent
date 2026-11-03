from types import SimpleNamespace
from pywebpush import WebPushException
from sqlmodel import select
from backend.db.models import PushSubscriptionDB
from backend.notification import push


def add_sub(session, user, endpoint):
    session.add(PushSubscriptionDB(user_id=user.id, endpoint=endpoint, p256dh="p", auth="a"))
    session.commit()


def fake_webpush(fail):
    """Returns a webpush stand-in. `fail` maps endpoint -> HTTP status to fail with."""
    calls = []

    def _webpush(subscription_info, **kwargs):
        endpoint = subscription_info["endpoint"]
        calls.append(endpoint)
        if endpoint in fail:
            raise WebPushException("push failed", response=SimpleNamespace(status_code=fail[endpoint], text=""))

    return _webpush, calls


def endpoints(session):
    return sorted(s.endpoint for s in session.exec(select(PushSubscriptionDB)).all())


def test_no_subscriptions_does_not_crash(session, user, monkeypatch):
    fake, calls = fake_webpush({})
    monkeypatch.setattr(push, "webpush", fake)
    assert push.send_push_notification(session, user.id, "t", "b") == 0
    assert calls == []


def test_every_device_gets_the_push(session, user, monkeypatch):
    add_sub(session, user, "phone")
    add_sub(session, user, "laptop")
    fake, calls = fake_webpush({})
    monkeypatch.setattr(push, "webpush", fake)
    assert push.send_push_notification(session, user.id, "t", "b") == 2
    assert sorted(calls) == ["laptop", "phone"]


def test_dead_subscription_is_deleted_and_others_still_sent(session, user, monkeypatch):
    add_sub(session, user, "gone")
    add_sub(session, user, "alive")
    fake, calls = fake_webpush({"gone": 410})
    monkeypatch.setattr(push, "webpush", fake)
    assert push.send_push_notification(session, user.id, "t", "b") == 1
    assert sorted(calls) == ["alive", "gone"]
    assert endpoints(session) == ["alive"]


def test_temporary_failure_keeps_the_subscription(session, user, monkeypatch):
    add_sub(session, user, "flaky")
    fake, _ = fake_webpush({"flaky": 500})
    monkeypatch.setattr(push, "webpush", fake)
    push.send_push_notification(session, user.id, "t", "b")
    assert endpoints(session) == ["flaky"]
