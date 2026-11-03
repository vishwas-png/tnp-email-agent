from urllib.parse import urlparse, parse_qs
import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.api import main
from backend.auth.encrypt import decrypt_token
from backend.auth.jwt_handler import create_access_token, create_refresh_token
from backend.db.database import get_session
from backend.db.models import User


class FakeCreds:
    def to_json(self):
        return json.dumps({"token": "fake-access", "refresh_token": "fake-refresh"})


class FakeFlow:
    def authorization_url(self, state, **kwargs):
        return f"https://accounts.google.com/o/oauth2/auth?state={state}", state

    def fetch_token(self, code):
        self.credentials = FakeCreds()


@pytest.fixture
def client(session, monkeypatch):
    main.app.dependency_overrides[get_session] = lambda: session
    monkeypatch.setattr(main, "make_flow", FakeFlow)
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def google_account(monkeypatch, email):
    monkeypatch.setattr(main, "get_account_email", lambda creds: email)


def start_login(client):
    response = client.get("/connect-gmail", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    return response, state


def test_connect_gmail_uses_random_state_in_short_lived_cookie(client):
    response, state = start_login(client)
    assert response.status_code == 307
    assert len(state) >= 32
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"oauth_state={state}")
    assert "Max-Age=600" in cookie and "HttpOnly" in cookie

    _, second_state = start_login(client)
    assert second_state != state


def test_callback_rejects_state_that_does_not_match_cookie(client, monkeypatch):
    google_account(monkeypatch, "student@example.com")
    start_login(client)
    response = client.get("/oauth/callback", params={"code": "c", "state": "forged"})
    assert response.status_code == 400


def test_callback_rejects_missing_state_cookie(client, monkeypatch):
    google_account(monkeypatch, "student@example.com")
    response = client.get("/oauth/callback", params={"code": "c", "state": "anything"})
    assert response.status_code == 400


def test_callback_handles_user_denying_consent(client):
    response = client.get("/oauth/callback", params={"error": "access_denied"})
    assert response.status_code == 400


def test_login_identity_comes_from_google_not_the_request(client, session, monkeypatch):
    # The victim exists. The attacker logs in with their own Google account.
    victim = User(email="victim@example.com", token_json=None)
    session.add(victim)
    session.commit()
    google_account(monkeypatch, "attacker@example.com")

    _, state = start_login(client)
    response = client.get("/oauth/callback", params={"code": "c", "state": state})

    assert response.status_code == 200
    assert response.json()["email"] == "attacker@example.com"
    session.refresh(victim)
    assert victim.token_json is None  # victim's Gmail token untouched
    attacker = session.exec(select(User).where(User.email == "attacker@example.com")).one()
    assert json.loads(decrypt_token(attacker.token_json))["refresh_token"] == "fake-refresh"


def test_login_sets_both_cookies_with_flags(client, monkeypatch):
    google_account(monkeypatch, "student@example.com")
    _, state = start_login(client)
    response = client.get("/oauth/callback", params={"code": "c", "state": state})

    cookies = response.headers.get_list("set-cookie")
    access = next(c for c in cookies if c.startswith("access_token="))
    refresh = next(c for c in cookies if c.startswith("refresh_token="))
    for cookie in (access, refresh):
        assert "HttpOnly" in cookie and "Path=/" in cookie and "SameSite=lax" in cookie
        assert "Secure" not in cookie  # COOKIE_SECURE is off by default for localhost
    assert "Max-Age=900" in access
    assert "Max-Age=2592000" in refresh


def test_secure_flag_follows_env_setting(client, monkeypatch):
    monkeypatch.setattr(main, "COOKIE_SECURE", True)
    response, _ = start_login(client)
    assert "Secure" in response.headers["set-cookie"]


def test_refresh_token_is_not_accepted_as_access_token(client, user):
    client.cookies.set("access_token", create_refresh_token(user.email))
    assert client.get("/notices").status_code == 401


def test_access_token_is_not_accepted_as_refresh_token(client, user):
    client.cookies.set("refresh_token", create_access_token(user.email))
    assert client.post("/refresh-token").status_code == 401


def test_refresh_is_post_only(client, user):
    client.cookies.set("refresh_token", create_refresh_token(user.email))
    assert client.get("/refresh-token").status_code == 405
    response = client.post("/refresh-token")
    assert response.status_code == 200
    assert response.headers["set-cookie"].startswith("access_token=")


def test_notices_are_scoped_to_the_logged_in_user(client, user):
    client.cookies.set("access_token", create_access_token(user.email))
    assert client.get("/notices").json() == []
    client.cookies.clear()
    assert client.get("/notices").status_code == 401
