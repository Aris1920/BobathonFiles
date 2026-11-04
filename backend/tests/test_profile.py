from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_token(client: TestClient, email: str = "profile_user@example.com") -> str:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_profile_creates_default(client: TestClient) -> None:
    """GET /profile auto-creates a default profile if one does not exist."""
    token = _register_and_token(client, "default_profile@example.com")
    resp = client.get("/profile", headers=_auth_headers(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["major"] == ""
    assert data["interests"] == []
    assert data["skills"] == []
    assert data["experience_level"] == "entry"
    assert data["savings"] == 0.0
    assert "id" in data
    assert "user_id" in data


def test_update_profile(client: TestClient) -> None:
    """PUT /profile updates specified fields and returns the updated profile."""
    token = _register_and_token(client, "update_profile@example.com")
    headers = _auth_headers(token)

    # Ensure profile exists first
    client.get("/profile", headers=headers)

    resp = client.put(
        "/profile",
        headers=headers,
        json={
            "major": "Computer Science",
            "interests": ["machine learning", "web dev"],
            "skills": ["Python", "React"],
            "experience_level": "mid",
            "savings": 5000.0,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["major"] == "Computer Science"
    assert data["interests"] == ["machine learning", "web dev"]
    assert data["skills"] == ["Python", "React"]
    assert data["experience_level"] == "mid"
    assert data["savings"] == 5000.0


def test_update_profile_invalid_experience_level(client: TestClient) -> None:
    """PUT /profile with an invalid experience_level returns 422."""
    token = _register_and_token(client, "invalid_exp@example.com")
    resp = client.put(
        "/profile",
        headers=_auth_headers(token),
        json={"experience_level": "expert"},
    )
    assert resp.status_code == 422
