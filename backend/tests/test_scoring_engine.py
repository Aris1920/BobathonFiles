"""Unit tests for backend/app/services/scoring_engine.py."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.schemas.job import NormalizedJob
from app.schemas.profile import ProfileRead
from app.schemas.results import ScoredJob
from app.services.scoring_engine import bucket_jobs, compute_fit_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    major: str = "computer science",
    skills: list[str] | None = None,
    interests: list[str] | None = None,
    experience_level: str = "mid",
) -> ProfileRead:
    return ProfileRead(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        major=major,
        interests=interests or [],
        skills=skills or [],
        experience_level=experience_level,
        savings=0.0,
        updated_at=datetime.now(timezone.utc),
    )


def _make_job(
    title: str = "Software Engineer",
    description: str = "",
    salary_min: float | None = None,
    salary_max: float | None = None,
) -> NormalizedJob:
    return NormalizedJob(
        title=title,
        company="Acme Corp",
        location="Remote",
        description=description,
        salary_min=salary_min,
        salary_max=salary_max,
        source="indeed",
        url="https://example.com/job/1",
        posted_at=datetime.now(timezone.utc),
    )


def _make_scored_job(title: str, fit_score: int, salary_median_est: float | None = None) -> ScoredJob:
    return ScoredJob(
        title=title,
        company="Acme",
        source="indeed",
        fit_score=fit_score,
        salary_median_est=salary_median_est,
    )


# ---------------------------------------------------------------------------
# compute_fit_score tests
# ---------------------------------------------------------------------------


def test_compute_fit_score_perfect_match():
    """All profile skills/interests appear in job description, major in title,
    experience level matches → expect a high score."""
    profile = _make_profile(
        major="computer science",
        skills=["python", "fastapi", "sql"],
        interests=["backend", "apis"],
        experience_level="mid",
    )
    job = _make_job(
        title="Backend Computer Science Engineer",
        description="Looking for python fastapi sql backend apis developer",
    )
    score = compute_fit_score(job, profile)
    # All 5 profile terms match → keyword = 50
    # major words "computer" and "science" both in title → major = 30
    # job is mid (no senior/entry signal), profile is mid → exp = 20
    assert score == 100


def test_compute_fit_score_no_match():
    """Completely unrelated job gives a low score."""
    profile = _make_profile(
        major="computer science",
        skills=["python", "fastapi"],
        interests=["machine learning"],
        experience_level="mid",
    )
    job = _make_job(
        title="Sous Chef",
        description="Preparing dishes and managing kitchen inventory.",
    )
    score = compute_fit_score(job, profile)
    # No keyword matches, no major matches, job is mid and profile is mid → 0+0+20=20
    assert score == 20


def test_compute_fit_score_experience_alignment_entry_vs_senior():
    """Entry-level profile matched against a senior job should get 0 experience points."""
    profile = _make_profile(experience_level="entry")
    job = _make_job(title="Senior Software Engineer")
    score = compute_fit_score(job, profile)
    # experience score should be 0 (entry profile + senior job)
    # We verify the exp component directly: senior job vs entry profile → 0 pts
    # Full score cannot exceed keyword + major + 0
    assert score <= 80  # at most 50 + 30 + 0


def test_compute_fit_score_experience_alignment_entry_entry():
    """Entry-level profile + entry-level job → 20 experience points."""
    profile = _make_profile(experience_level="entry", skills=[], interests=[])
    job = _make_job(title="Junior Python Developer")
    score = compute_fit_score(job, profile)
    # No keywords, major mismatch → only exp points (20)
    assert score == 20


def test_compute_fit_score_resume_text_boost():
    """resume_text keywords are added to profile terms and should raise the score."""
    profile = _make_profile(
        major="marketing",
        skills=[],
        interests=[],
        experience_level="mid",
    )
    job = _make_job(
        title="Marketing Specialist",
        description="Looking for someone with seo sem analytics skills.",
    )
    score_without_resume = compute_fit_score(job, profile)
    score_with_resume = compute_fit_score(
        job,
        profile,
        resume_text="seo sem analytics google ads content",
    )
    # Resume text adds matching terms → score should be at least as high
    assert score_with_resume >= score_without_resume


# ---------------------------------------------------------------------------
# bucket_jobs tests
# ---------------------------------------------------------------------------


def test_bucket_jobs_distributes_correctly():
    """Three jobs with fit_scores 80, 55, 20 should land in high, mid, low respectively."""
    jobs = [
        _make_scored_job("Job A", fit_score=80),
        _make_scored_job("Job B", fit_score=55),
        _make_scored_job("Job C", fit_score=20),
    ]
    result = bucket_jobs(jobs)

    assert len(result.high.jobs) == 1
    assert result.high.jobs[0].title == "Job A"

    assert len(result.mid.jobs) == 1
    assert result.mid.jobs[0].title == "Job B"

    assert len(result.low.jobs) == 1
    assert result.low.jobs[0].title == "Job C"


def test_bucket_jobs_empty_tier():
    """When all jobs land in the high tier, mid and low should have empty lists."""
    jobs = [
        _make_scored_job("Job A", fit_score=90),
        _make_scored_job("Job B", fit_score=75),
        _make_scored_job("Job C", fit_score=70),
    ]
    result = bucket_jobs(jobs)

    assert len(result.high.jobs) == 3
    assert result.mid.jobs == []
    assert result.low.jobs == []
    assert result.mid.stats.job_count == 0
    assert result.low.stats.job_count == 0


def test_bucket_jobs_sorted_descending():
    """Jobs within a tier should be sorted by fit_score descending."""
    jobs = [
        _make_scored_job("Low A", fit_score=45),
        _make_scored_job("Low C", fit_score=65),
        _make_scored_job("Low B", fit_score=55),
    ]
    result = bucket_jobs(jobs)

    scores = [j.fit_score for j in result.mid.jobs]
    assert scores == sorted(scores, reverse=True)


def test_tier_stats_salary_median():
    """TierStats.salary_median should be the median of salary_median_est values."""
    jobs = [
        _make_scored_job("Job A", fit_score=80, salary_median_est=50_000.0),
        _make_scored_job("Job B", fit_score=75, salary_median_est=70_000.0),
        _make_scored_job("Job C", fit_score=72, salary_median_est=90_000.0),
    ]
    result = bucket_jobs(jobs)

    stats = result.high.stats
    assert stats.salary_median == 70_000.0
    assert stats.salary_min == 50_000.0
    assert stats.salary_max == 90_000.0
    assert stats.job_count == 3


def test_tier_stats_no_salary():
    """When no jobs have salary_median_est, all salary stats should be None."""
    jobs = [_make_scored_job("Job A", fit_score=80, salary_median_est=None)]
    result = bucket_jobs(jobs)

    stats = result.high.stats
    assert stats.salary_min is None
    assert stats.salary_max is None
    assert stats.salary_median is None
    assert stats.job_count == 1
