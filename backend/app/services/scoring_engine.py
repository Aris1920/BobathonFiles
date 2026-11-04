from __future__ import annotations

import re
import statistics

from app.schemas.job import NormalizedJob
from app.schemas.profile import ProfileRead
from app.schemas.results import JobTier, ScoredJob, TierStats, TieredResults
from app.services import salary_service

# ---------------------------------------------------------------------------
# Fit score computation
# ---------------------------------------------------------------------------

_ENTRY_SIGNALS = {"junior", "entry", "associate", "intern", "trainee", "i ", " i"}
_SENIOR_SIGNALS = {
    "senior",
    "sr.",
    "lead",
    "principal",
    "staff",
    "director",
    "manager",
    "head of",
    "vp",
    "chief",
}


def _detect_job_level(title_lower: str) -> str:
    """Return 'entry', 'senior', or 'mid' based on signals in the job title."""
    for sig in _SENIOR_SIGNALS:
        if sig in title_lower:
            return "senior"
    for sig in _ENTRY_SIGNALS:
        if sig in title_lower:
            return "entry"
    return "mid"


def compute_fit_score(
    job: NormalizedJob,
    profile: ProfileRead,
    resume_text: str | None = None,
) -> int:
    """Compute a fit score (0–100) for a job against a user profile.

    Breakdown:
    - Keyword overlap (up to 50 points)
    - Major relevance (up to 30 points)
    - Experience level alignment (up to 20 points)
    """
    # --- 1. Keyword overlap (up to 50 points) ---
    profile_terms: set[str] = set()
    for term in profile.skills + profile.interests:
        stripped = term.lower().strip()
        if stripped:
            profile_terms.add(stripped)

    if resume_text:
        # Extract words longer than 3 characters from resume
        words = re.split(r"[\s\W]+", resume_text.lower())
        for word in words:
            if len(word) > 3:
                profile_terms.add(word)

    job_text = (job.title + " " + (job.description or "")).lower()

    matches = sum(1 for term in profile_terms if term in job_text)
    keyword_score = min(50, int((matches / max(1, len(profile_terms))) * 50))

    # --- 2. Major relevance (up to 30 points) ---
    major_words = [w for w in profile.major.lower().split() if w]
    title_lower = job.title.lower()
    major_matches = sum(1 for word in major_words if word in title_lower)
    major_score = min(30, int((major_matches / max(1, len(major_words))) * 30))

    # --- 3. Experience level alignment (up to 20 points) ---
    job_level = _detect_job_level(title_lower)
    exp = profile.experience_level

    if exp == "entry":
        exp_score = 20 if job_level == "entry" else (10 if job_level == "mid" else 0)
    elif exp == "mid":
        exp_score = 20 if job_level == "mid" else 10
    else:  # senior
        exp_score = 20 if job_level == "senior" else (10 if job_level == "mid" else 0)

    total = keyword_score + major_score + exp_score
    return max(0, min(100, total))


# ---------------------------------------------------------------------------
# Score + enrich jobs with salary estimates
# ---------------------------------------------------------------------------


async def score_and_enrich_jobs(
    jobs: list[NormalizedJob],
    profile: ProfileRead,
    bls_api_key: str,
    resume_text: str | None = None,
) -> list[ScoredJob]:
    """Compute fit scores and salary estimates for every job.

    BLS salary lookups are cached by job title so each unique title only
    triggers one API call.
    """
    salary_cache: dict[str, float | None] = {}
    scored: list[ScoredJob] = []

    for job in jobs:
        fit_score = compute_fit_score(job, profile, resume_text)

        if job.salary_min is not None and job.salary_max is not None:
            salary_median_est: float | None = (job.salary_min + job.salary_max) / 2
        else:
            title_key = job.title.lower().strip()
            if title_key not in salary_cache:
                salary_cache[title_key] = await salary_service.estimate_salary(
                    job.title, bls_api_key
                )
            salary_median_est = salary_cache[title_key]

        scored.append(
            ScoredJob(
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                source=job.source,
                url=job.url,
                posted_at=job.posted_at,
                fit_score=fit_score,
                salary_median_est=salary_median_est,
            )
        )

    return scored


# ---------------------------------------------------------------------------
# Tier bucketing
# ---------------------------------------------------------------------------


def _compute_tier_stats(jobs: list[ScoredJob]) -> TierStats:
    """Compute salary statistics across all jobs in a tier."""
    salaries = [j.salary_median_est for j in jobs if j.salary_median_est is not None]

    if salaries:
        return TierStats(
            salary_min=min(salaries),
            salary_max=max(salaries),
            salary_median=statistics.median(salaries),
            job_count=len(jobs),
        )
    return TierStats(
        salary_min=None,
        salary_max=None,
        salary_median=None,
        job_count=len(jobs),
    )


def bucket_jobs(scored_jobs: list[ScoredJob]) -> TieredResults:
    """Split scored jobs into High / Mid / Low tiers by fit_score.

    High  >= 70
    Mid   >= 40 and < 70
    Low   <  40

    Each tier is sorted by fit_score descending.
    """
    high_jobs = sorted(
        [j for j in scored_jobs if j.fit_score >= 70],
        key=lambda j: j.fit_score,
        reverse=True,
    )
    mid_jobs = sorted(
        [j for j in scored_jobs if 40 <= j.fit_score < 70],
        key=lambda j: j.fit_score,
        reverse=True,
    )
    low_jobs = sorted(
        [j for j in scored_jobs if j.fit_score < 40],
        key=lambda j: j.fit_score,
        reverse=True,
    )

    return TieredResults(
        high=JobTier(tier="high", jobs=high_jobs, stats=_compute_tier_stats(high_jobs)),
        mid=JobTier(tier="mid", jobs=mid_jobs, stats=_compute_tier_stats(mid_jobs)),
        low=JobTier(tier="low", jobs=low_jobs, stats=_compute_tier_stats(low_jobs)),
    )
