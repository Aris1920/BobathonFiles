"""Tests for job board adapter layer and the aggregator service.

All external HTTP calls are mocked via respx so no real API keys are needed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import respx
from httpx import Response

from app.config import Settings
from app.schemas.job import NormalizedJob
from app.schemas.profile import ProfileRead
from app.services.job_adapters import indeed, usajobs
from app.services.job_aggregator import fetch_jobs, _build_keywords


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile(**overrides) -> ProfileRead:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        major="Computer Science",
        interests=["machine learning", "data science"],
        skills=["Python", "SQL"],
        experience_level="entry",
        savings=5000.0,
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return ProfileRead(**defaults)


def _make_settings(**overrides) -> Settings:
    """Return a Settings instance with dummy API keys unless overridden."""
    # Use model_construct to bypass env-file loading in tests.
    data = dict(
        database_url="sqlite://",
        secret_key="test-secret",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        algorithm="HS256",
        linkedin_client_id="li-id",
        linkedin_client_secret="li-secret",
        handshake_api_key="hs-key",
        indeed_publisher_id="indeed-pub",
        usajobs_api_key="usa-key",
        bls_api_key="bls-key",
    )
    data.update(overrides)
    return Settings.model_construct(**data)


# ---------------------------------------------------------------------------
# test_usajobs_search_returns_normalized_jobs
# ---------------------------------------------------------------------------

USAJOBS_MOCK_RESPONSE = {
    "SearchResult": {
        "SearchResultItems": [
            {
                "MatchedObjectDescriptor": {
                    "PositionTitle": "Software Engineer",
                    "OrganizationName": "Department of Defense",
                    "PositionLocationDisplay": "Washington, DC",
                    "UserArea": {
                        "Details": {
                            "JobSummary": "Develop software systems for national defense."
                        }
                    },
                    "PositionRemuneration": [
                        {"MinimumRange": "80000", "MaximumRange": "120000"}
                    ],
                    "PositionURI": "https://www.usajobs.gov/job/12345",
                    "PublicationStartDate": "2025-03-01",
                }
            }
        ]
    }
}


@pytest.mark.asyncio
@respx.mock
async def test_usajobs_search_returns_normalized_jobs():
    respx.get("https://data.usajobs.gov/api/Search").mock(
        return_value=Response(200, json=USAJOBS_MOCK_RESPONSE)
    )

    jobs = await usajobs.search("software engineer", "United States", "test-key")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Software Engineer"
    assert job.company == "Department of Defense"
    assert job.location == "Washington, DC"
    assert job.description == "Develop software systems for national defense."
    assert job.salary_min == 80000.0
    assert job.salary_max == 120000.0
    assert job.source == "usajobs"
    assert job.url == "https://www.usajobs.gov/job/12345"
    assert job.posted_at == datetime(2025, 3, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# test_indeed_search_returns_normalized_jobs
# ---------------------------------------------------------------------------

INDEED_MOCK_RESPONSE = {
    "results": [
        {
            "jobtitle": "Data Analyst",
            "company": "Acme Corp",
            "formattedLocation": "New York, NY",
            "snippet": "Analyze data to drive business decisions.",
            "url": "https://www.indeed.com/viewjob?jk=abc123",
            "date": "Wed, 05 Mar 2025 08:00:00 GMT",
        }
    ]
}


@pytest.mark.asyncio
@respx.mock
async def test_indeed_search_returns_normalized_jobs():
    respx.get("https://api.indeed.com/ads/apisearch").mock(
        return_value=Response(200, json=INDEED_MOCK_RESPONSE)
    )

    jobs = await indeed.search("data analyst", "United States", "pub-123")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Data Analyst"
    assert job.company == "Acme Corp"
    assert job.location == "New York, NY"
    assert job.description == "Analyze data to drive business decisions."
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.source == "indeed"
    assert job.url == "https://www.indeed.com/viewjob?jk=abc123"
    assert job.posted_at == datetime(2025, 3, 5, 8, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# test_adapter_skips_when_no_api_key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adapter_skips_when_no_api_key_usajobs():
    jobs = await usajobs.search("anything", "United States", "")
    assert jobs == []


@pytest.mark.asyncio
async def test_adapter_skips_when_no_api_key_indeed():
    jobs = await indeed.search("anything", "United States", "")
    assert jobs == []


@pytest.mark.asyncio
async def test_adapter_skips_when_no_api_key_none_usajobs():
    jobs = await usajobs.search("anything", "United States", None)  # type: ignore[arg-type]
    assert jobs == []


@pytest.mark.asyncio
async def test_adapter_skips_when_no_api_key_none_indeed():
    jobs = await indeed.search("anything", "United States", None)  # type: ignore[arg-type]
    assert jobs == []


# ---------------------------------------------------------------------------
# test_aggregator_deduplication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_aggregator_deduplication():
    """Same job title+company returned by two sources → only one in the result."""
    # USAJobs returns "Software Engineer" at "Dept of Defense"
    respx.get("https://data.usajobs.gov/api/Search").mock(
        return_value=Response(200, json=USAJOBS_MOCK_RESPONSE)
    )
    # Indeed returns the same title+company (simulated duplicate)
    indeed_duplicate = {
        "results": [
            {
                "jobtitle": "Software Engineer",
                "company": "Department of Defense",
                "formattedLocation": "Washington, DC",
                "snippet": "Duplicate listing from Indeed.",
                "url": "https://www.indeed.com/viewjob?jk=dup",
                "date": "Wed, 05 Mar 2025 08:00:00 GMT",
            }
        ]
    }
    respx.get("https://api.indeed.com/ads/apisearch").mock(
        return_value=Response(200, json=indeed_duplicate)
    )
    # LinkedIn and Handshake return nothing (no key)
    respx.get("https://api.linkedin.com/v2/jobSearch").mock(
        return_value=Response(200, json={"elements": []})
    )
    respx.get("https://app.joinhandshake.com/api/v1/jobs").mock(
        return_value=Response(200, json={"results": []})
    )

    profile = _make_profile()
    settings = _make_settings()

    jobs = await fetch_jobs(profile, settings)

    # Only one of the two identical (title, company) pairs should survive
    sw_eng_dod = [
        j for j in jobs
        if j.title.lower() == "software engineer"
        and j.company == "Department of Defense"
    ]
    assert len(sw_eng_dod) == 1


# ---------------------------------------------------------------------------
# test_aggregator_handles_one_source_failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_aggregator_handles_one_source_failure():
    """One adapter raising an HTTP error should not prevent others from returning."""
    # USAJobs returns a valid result
    respx.get("https://data.usajobs.gov/api/Search").mock(
        return_value=Response(200, json=USAJOBS_MOCK_RESPONSE)
    )
    # Indeed returns a 500 error
    respx.get("https://api.indeed.com/ads/apisearch").mock(
        return_value=Response(500)
    )
    # LinkedIn returns empty
    respx.get("https://api.linkedin.com/v2/jobSearch").mock(
        return_value=Response(200, json={"elements": []})
    )
    # Handshake returns empty
    respx.get("https://app.joinhandshake.com/api/v1/jobs").mock(
        return_value=Response(200, json={"results": []})
    )

    profile = _make_profile()
    settings = _make_settings()

    # Should not raise; USAJobs result should still come through
    jobs = await fetch_jobs(profile, settings)

    assert any(j.source == "usajobs" for j in jobs)
    # Indeed failed gracefully — no indeed jobs
    assert not any(j.source == "indeed" for j in jobs)


# ---------------------------------------------------------------------------
# test _build_keywords helper
# ---------------------------------------------------------------------------

def test_build_keywords_deduplication_and_max():
    """Keywords are deduplicated and capped at 10 terms."""
    # Use single-word terms so splitting the result string is unambiguous.
    profile = _make_profile(
        major="Python",  # already in skills — should deduplicate
        skills=["Python", "SQL", "Java", "Go", "Rust", "Scala", "TypeScript"],
        interests=["Statistics", "Kubernetes", "Networking"],
    )
    keywords = _build_keywords(profile)
    # Each term is a single word, so splitting by space gives one entry per term.
    terms = keywords.split(" ")
    # No duplicates (case-insensitive)
    assert len(terms) == len(set(t.lower() for t in terms))
    # At most 10 terms (major deduplicates with first skill → 9 unique items → all fit; cap not hit, but still ≤ 10)
    assert len(terms) <= 10

    # Also verify the cap with 12 distinct single-word skills
    profile_large = _make_profile(
        major="Biology",
        skills=["C", "Go", "Rust", "Java", "Scala", "SQL", "TypeScript", "Python", "R", "MATLAB"],
        interests=["DevOps", "Security"],
    )
    keywords_large = _build_keywords(profile_large)
    terms_large = keywords_large.split(" ")
    assert len(terms_large) <= 10
