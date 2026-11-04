"""Tests for POST /results/generate and GET /results/latest."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.job import NormalizedJob
from app.schemas.results import ScoredJob

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

_GENERATE_URL = "/results/generate"
_LATEST_URL = "/results/latest"

_VALID_LOAN = {
    "label": "Federal Direct Subsidized",
    "loan_type": "federal_subsidized",
    "balance": 15_000.0,
    "annual_interest_rate": 0.055,
    "minimum_monthly_payment": 150.0,
}

_VALID_PROFILE = {
    "major": "Computer Science",
    "skills": ["Python", "SQL"],
    "interests": ["software", "data"],
    "experience_level": "entry",
    "savings": 5000.0,
}


def _register_and_token(client: TestClient, email: str) -> str:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_scored_jobs(count: int = 5) -> list[ScoredJob]:
    """Return a list of ScoredJob objects with varying fit scores."""
    # Spread scores across tiers: high (>=70), mid (40-69), low (<40)
    score_ladder = [80, 75, 55, 45, 25]
    jobs = []
    for i in range(count):
        score = score_ladder[i % len(score_ladder)]
        jobs.append(
            ScoredJob(
                title=f"Test Job {i}",
                company="Test Co",
                location="USA",
                description=f"Python SQL software entry level job {i}",
                salary_min=50_000.0,
                salary_max=70_000.0,
                source="usajobs",
                url=None,
                posted_at=None,
                fit_score=score,
                salary_median_est=60_000.0,
            )
        )
    return jobs


def _make_normalized_jobs(count: int = 5) -> list[NormalizedJob]:
    """Return NormalizedJob stubs (before scoring)."""
    return [
        NormalizedJob(
            title=f"Test Job {i}",
            company="Test Co",
            location="USA",
            description=f"Python SQL software entry level job {i}",
            salary_min=50_000.0,
            salary_max=70_000.0,
            source="usajobs",
            url=None,
            posted_at=None,
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# test_generate_requires_loans
# ---------------------------------------------------------------------------


def test_generate_requires_loans(client: TestClient) -> None:
    """POST /results/generate returns 422 if user has no loans."""
    token = _register_and_token(client, "gen_noloan@example.com")
    headers = _auth_headers(token)

    # Set profile but do NOT add any loans
    client.put("/profile", headers=headers, json=_VALID_PROFILE)

    resp = client.post(_GENERATE_URL, headers=headers, json={})
    assert resp.status_code == 422
    assert "student loan" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# test_generate_returns_three_tiers
# ---------------------------------------------------------------------------


def test_generate_returns_three_tiers(client: TestClient) -> None:
    """POST /results/generate returns high/mid/low tiers with projections."""
    token = _register_and_token(client, "gen_tiers@example.com")
    headers = _auth_headers(token)

    # Setup: profile + loan
    client.put("/profile", headers=headers, json=_VALID_PROFILE)
    client.post("/loans", headers=headers, json=_VALID_LOAN)

    normalized = _make_normalized_jobs(5)
    scored = _make_scored_jobs(5)

    with (
        patch(
            "app.routers.results.fetch_jobs",
            new=AsyncMock(return_value=normalized),
        ),
        patch(
            "app.routers.results.score_and_enrich_jobs",
            new=AsyncMock(return_value=scored),
        ),
    ):
        resp = client.post(_GENERATE_URL, headers=headers, json={"savings_rate_pct": 20.0})

    assert resp.status_code == 200
    body = resp.json()

    # Top-level keys
    assert "high" in body
    assert "mid" in body
    assert "low" in body
    assert "generated_at" in body

    # Each tier has jobs list and projection with months_to_payoff > 0
    for tier_key in ("high", "mid", "low"):
        tier = body[tier_key]
        assert "jobs" in tier
        assert isinstance(tier["jobs"], list)
        assert "projection" in tier
        assert tier["projection"]["months_to_payoff"] > 0


# ---------------------------------------------------------------------------
# test_generate_uses_demo_jobs_when_no_api_jobs
# ---------------------------------------------------------------------------


def test_generate_uses_demo_jobs_when_no_api_jobs(client: TestClient) -> None:
    """When fetch_jobs returns [], demo stubs are generated and results are valid."""
    token = _register_and_token(client, "gen_demo@example.com")
    headers = _auth_headers(token)

    client.put("/profile", headers=headers, json=_VALID_PROFILE)
    client.post("/loans", headers=headers, json=_VALID_LOAN)

    with patch(
        "app.routers.results.fetch_jobs",
        new=AsyncMock(return_value=[]),
    ):
        resp = client.post(_GENERATE_URL, headers=headers, json={})

    assert resp.status_code == 200
    body = resp.json()

    # Should still have all three tiers
    for tier_key in ("high", "mid", "low"):
        assert tier_key in body

    # Aggregate job count across tiers should be 10 (the demo stubs)
    total_jobs = sum(len(body[t]["jobs"]) for t in ("high", "mid", "low"))
    assert total_jobs == 10

    # Projections must have positive months
    for tier_key in ("high", "mid", "low"):
        assert body[tier_key]["projection"]["months_to_payoff"] > 0


# ---------------------------------------------------------------------------
# test_get_latest_returns_404_when_no_results
# ---------------------------------------------------------------------------


def test_get_latest_returns_404_when_no_results(client: TestClient) -> None:
    """GET /results/latest returns 404 when the user has never generated results."""
    token = _register_and_token(client, "latest_empty@example.com")
    headers = _auth_headers(token)

    resp = client.get(_LATEST_URL, headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# test_get_latest_returns_saved_results
# ---------------------------------------------------------------------------


def test_get_latest_returns_saved_results(client: TestClient) -> None:
    """GET /results/latest returns 200 with saved results after a generate call."""
    token = _register_and_token(client, "latest_saved@example.com")
    headers = _auth_headers(token)

    client.put("/profile", headers=headers, json=_VALID_PROFILE)
    client.post("/loans", headers=headers, json=_VALID_LOAN)

    normalized = _make_normalized_jobs(5)
    scored = _make_scored_jobs(5)

    with (
        patch(
            "app.routers.results.fetch_jobs",
            new=AsyncMock(return_value=normalized),
        ),
        patch(
            "app.routers.results.score_and_enrich_jobs",
            new=AsyncMock(return_value=scored),
        ),
    ):
        gen_resp = client.post(_GENERATE_URL, headers=headers, json={})

    assert gen_resp.status_code == 200

    # Now GET /results/latest should return 200
    latest_resp = client.get(_LATEST_URL, headers=headers)
    assert latest_resp.status_code == 200

    body = latest_resp.json()
    assert "high" in body
    assert "mid" in body
    assert "low" in body
    assert "generated_at" in body
