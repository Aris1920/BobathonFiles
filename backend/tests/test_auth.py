"""Tests for the /auth endpoints (register, login, refresh)."""
from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
REFRESH_URL = "/auth/refresh"

_USER_EMAIL = "alice@example.com"
_USER_PASSWORD = "securepass1"


def _register(client: TestClient, email: str = _USER_EMAIL, password: str = _USER_PASSWORD):
    return client.post(REGISTER_URL, json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


def test_register_success(client: TestClient):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient):
    _register(client)
    resp = _register(client)  # second attempt — same email
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_short_password(client: TestClient):
    resp = client.post(REGISTER_URL, json={"email": "bob@example.com", "password": "short"})
    assert resp.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success(client: TestClient):
    _register(client)
    resp = client.post(LOGIN_URL, json={"email": _USER_EMAIL, "password": _USER_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    _register(client)
    resp = client.post(LOGIN_URL, json={"email": _USER_EMAIL, "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "somepassword"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


def test_refresh_token(client: TestClient):
    tokens = _register(client).json()
    resp = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_refresh_with_access_token_fails(client: TestClient):
    """Passing an access token to /refresh should be rejected (wrong type)."""
    tokens = _register(client).json()
    resp = client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_refresh_with_invalid_token(client: TestClient):
    resp = client.post(REFRESH_URL, json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401
