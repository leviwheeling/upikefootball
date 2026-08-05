from fastapi.testclient import TestClient

from app.auth import SESSION_SECONDS, create_session_token, valid_session_token
from app.main import app, settings


def test_session_token_is_signed_and_expires() -> None:
    token = create_session_token("coach-secret", now=1_000)

    assert valid_session_token(token, "coach-secret", now=1_001)
    assert valid_session_token(token, "coach-secret", now=1_000 + SESSION_SECONDS - 1)
    assert not valid_session_token(token, "wrong-secret", now=1_001)
    assert not valid_session_token(token, "coach-secret", now=1_000 + SESSION_SECONDS)
    assert not valid_session_token("broken", "coach-secret", now=1_001)


def test_password_protects_pages_and_api(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(settings, "site_password", "coach-secret")
    monkeypatch.setattr(settings, "environment", "development")

    with TestClient(app) as client:
        page = client.get("/")
        api = client.get("/api/stat-board")
        failed = client.post(
            "/login",
            data={"password": "wrong", "next": "/"},
            follow_redirects=False,
        )
        login = client.post(
            "/login",
            data={"password": "coach-secret", "next": "/api/stat-board"},
            follow_redirects=False,
        )
        authenticated = client.get("/api/stat-board")

    assert page.status_code == 401
    assert "Restricted analytics" in page.text
    assert api.status_code == 401
    assert api.json()["detail"]["code"] == "authentication_required"
    assert failed.status_code == 401
    assert "Incorrect password" in failed.text
    assert login.status_code == 303
    assert login.headers["location"] == "/api/stat-board"
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=lax" in login.headers["set-cookie"]
    assert f"Max-Age={SESSION_SECONDS}" in login.headers["set-cookie"]
    assert authenticated.status_code == 200


def test_production_fails_closed_without_password(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(settings, "site_password", None)
    monkeypatch.setattr(settings, "environment", "production")

    with TestClient(app) as client:
        health = client.get("/api/health")
        page = client.get("/")

    assert health.status_code == 200
    assert page.status_code == 503
    assert "environment variable named password" in page.text
