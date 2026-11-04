"""Results router — orchestrates the full job-fetch → score → tier → project pipeline."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, settings as _default_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.debt_projection import DebtProjection
from app.models.job_result import JobResult
from app.models.profile import Profile
from app.models.student_loan import StudentLoan
from app.models.user import User
from app.schemas.job import NormalizedJob
from app.schemas.loan import LoanRead
from app.schemas.profile import ProfileRead
from app.schemas.projection import ProjectionResult
from app.schemas.results import (
    GenerateRequest,
    ResultsResponse,
    ScoredJob,
    TierStats,
    TieredResults,
    TierWithProjection,
)
from app.services.debt_projection import project_payoff
from app.services.job_aggregator import fetch_jobs
from app.services.scoring_engine import bucket_jobs, score_and_enrich_jobs

router = APIRouter(prefix="/results", tags=["results"])

# ---------------------------------------------------------------------------
# Salary fallbacks per tier when no salary data is available
# ---------------------------------------------------------------------------
_TIER_SALARY_FALLBACK: dict[str, float] = {
    "high": 85_000.0,
    "mid": 60_000.0,
    "low": 45_000.0,
}

# ---------------------------------------------------------------------------
# Demo job stubs (used when no real API jobs are returned)
# ---------------------------------------------------------------------------

_DEMO_DESCRIPTION = "Demo listing — configure API keys to see real job results."


def _make_demo_jobs(major: str, skills: list[str]) -> list[NormalizedJob]:
    """Return 10 synthetic NormalizedJob stubs for demo purposes.

    Salary ranges are broad illustrative figures drawn from BLS data for
    common fields.  The company name is explicitly marked as "Demo Inc."
    so users know these are placeholders.
    """
    primary_skill = skills[0] if skills else major

    templates: list[tuple[str, float, float]] = [
        (f"Entry {major} Analyst", 42_000, 58_000),
        (f"Junior {major} Specialist", 45_000, 60_000),
        (f"Associate {primary_skill} Developer", 50_000, 68_000),
        (f"{major} Coordinator", 38_000, 52_000),
        (f"Junior {primary_skill} Engineer", 55_000, 75_000),
        (f"{major} Assistant", 35_000, 48_000),
        (f"Entry-Level {major} Consultant", 48_000, 65_000),
        (f"Associate {major} Researcher", 44_000, 62_000),
        (f"Junior {primary_skill} Analyst", 46_000, 64_000),
        (f"{major} Technician", 36_000, 50_000),
    ]

    return [
        NormalizedJob(
            title=title,
            company="Demo Inc.",
            location="United States",
            description=_DEMO_DESCRIPTION,
            salary_min=sal_min,
            salary_max=sal_max,
            source="usajobs",
            url=None,
            posted_at=None,
        )
        for title, sal_min, sal_max in templates
    ]


# ---------------------------------------------------------------------------
# Helper: load profile and loans for the current user
# ---------------------------------------------------------------------------


def _load_profile(user: User, db: Session) -> ProfileRead:
    profile: Profile | None = (
        db.query(Profile).filter(Profile.user_id == user.id).first()
    )
    if profile is None:
        # Auto-create a blank profile so the error message is about loans
        profile = Profile(
            user_id=user.id,
            major="",
            interests=[],
            skills=[],
            experience_level="entry",
            savings=0.0,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ProfileRead.model_validate(profile, from_attributes=True)


def _load_loans(user: User, db: Session) -> list[LoanRead]:
    rows = db.query(StudentLoan).filter(StudentLoan.user_id == user.id).all()
    return [LoanRead.model_validate(r, from_attributes=True) for r in rows]


# ---------------------------------------------------------------------------
# POST /results/generate
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=ResultsResponse, status_code=status.HTTP_200_OK)
async def generate_results(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    app_settings: Settings = Depends(lambda: _default_settings),
) -> ResultsResponse:
    """Run the full pipeline: fetch jobs → score → tier → project debt payoff → persist."""

    # 1. Load profile and loans
    profile = _load_profile(current_user, db)
    loans = _load_loans(current_user, db)

    # 2. Validate: at least one loan is required
    if not loans:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please add at least one student loan before generating results.",
        )

    # 3. Fetch jobs from external sources
    jobs = await fetch_jobs(profile, app_settings)

    # 4. If no jobs came back, generate demo stubs
    if not jobs:
        jobs = _make_demo_jobs(profile.major, list(profile.skills))

    # 5. Score and enrich
    scored_jobs = await score_and_enrich_jobs(
        jobs, profile, app_settings.bls_api_key, body.resume_text
    )

    # 6. Bucket into tiers
    tiered: TieredResults = bucket_jobs(scored_jobs)

    # 7. Project payoff per tier and build response tiers
    generated_at = datetime.utcnow()

    tiers_with_projection: dict[str, TierWithProjection] = {}
    for tier_name in ("high", "mid", "low"):
        job_tier = getattr(tiered, tier_name)
        salary = (
            job_tier.stats.salary_median
            if job_tier.stats.salary_median is not None
            else _TIER_SALARY_FALLBACK[tier_name]
        )
        projection: ProjectionResult = project_payoff(loans, salary, body.savings_rate_pct)
        tiers_with_projection[tier_name] = TierWithProjection(
            tier=tier_name,  # type: ignore[arg-type]
            jobs=job_tier.jobs,
            stats=job_tier.stats,
            projection=projection,
        )

    # 8. Persist job results (one add() per row to stay compatible with SQLite test engine)
    for tier_name in ("high", "mid", "low"):
        for job in tiers_with_projection[tier_name].jobs:
            db.add(
                JobResult(
                    user_id=current_user.id,
                    created_at=generated_at,
                    tier=tier_name,
                    job_title=job.title,
                    company=job.company,
                    location=job.location,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max,
                    salary_median_est=job.salary_median_est,
                    source=job.source,
                    job_url=job.url,
                    fit_score=job.fit_score,
                )
            )

    # 9. Persist three DebtProjection rows
    for tier_name in ("high", "mid", "low"):
        twp = tiers_with_projection[tier_name]
        salary_used = (
            twp.stats.salary_median
            if twp.stats.salary_median is not None
            else _TIER_SALARY_FALLBACK[tier_name]
        )
        db.add(
            DebtProjection(
                user_id=current_user.id,
                created_at=generated_at,
                tier=tier_name,
                median_salary_used=salary_used,
                savings_rate_pct=body.savings_rate_pct,
                months_to_payoff=twp.projection.months_to_payoff,
                total_interest_paid=twp.projection.total_interest_paid,
            )
        )

    db.commit()

    return ResultsResponse(
        high=tiers_with_projection["high"],
        mid=tiers_with_projection["mid"],
        low=tiers_with_projection["low"],
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------------
# GET /results/latest
# ---------------------------------------------------------------------------


@router.get("/latest", response_model=ResultsResponse)
def get_latest_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResultsResponse:
    """Return the most recently generated results for the current user."""

    # Find the most recent created_at across job_results for this user
    from sqlalchemy import func

    latest_ts = (
        db.query(func.max(JobResult.created_at))
        .filter(JobResult.user_id == current_user.id)
        .scalar()
    )

    if latest_ts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found. Call POST /results/generate first.",
        )

    # Load all job results at that timestamp
    job_rows = (
        db.query(JobResult)
        .filter(JobResult.user_id == current_user.id, JobResult.created_at == latest_ts)
        .all()
    )

    # Load debt projections closest to that timestamp (one per tier)
    proj_rows = (
        db.query(DebtProjection)
        .filter(DebtProjection.user_id == current_user.id, DebtProjection.created_at == latest_ts)
        .all()
    )

    # Index projections by tier
    proj_by_tier: dict[str, DebtProjection] = {r.tier: r for r in proj_rows}

    # Reconstruct tiers
    tiers_with_projection: dict[str, TierWithProjection] = {}
    for tier_name in ("high", "mid", "low"):
        tier_jobs = [jr for jr in job_rows if jr.tier == tier_name]

        scored_jobs = [
            ScoredJob(
                title=jr.job_title,
                company=jr.company,
                location=jr.location,
                description=None,
                salary_min=float(jr.salary_min) if jr.salary_min is not None else None,
                salary_max=float(jr.salary_max) if jr.salary_max is not None else None,
                source=jr.source,
                url=jr.job_url,
                posted_at=None,
                fit_score=jr.fit_score or 0,
                salary_median_est=(
                    float(jr.salary_median_est) if jr.salary_median_est is not None else None
                ),
            )
            for jr in tier_jobs
        ]

        # Recompute stats from stored data
        salaries = [j.salary_median_est for j in scored_jobs if j.salary_median_est is not None]
        import statistics as _stats
        stats = TierStats(
            salary_min=min(salaries) if salaries else None,
            salary_max=max(salaries) if salaries else None,
            salary_median=_stats.median(salaries) if salaries else None,
            job_count=len(scored_jobs),
        )

        # Reconstruct projection from stored row (no monthly breakdown available)
        proj_row = proj_by_tier.get(tier_name)
        if proj_row:
            projection = ProjectionResult(
                months_to_payoff=proj_row.months_to_payoff or 0,
                total_interest_paid=float(proj_row.total_interest_paid or 0),
                monthly_payment_applied=0.0,
                monthly_take_home=0.0,
                monthly_breakdown=[],
            )
        else:
            projection = ProjectionResult(
                months_to_payoff=0,
                total_interest_paid=0.0,
                monthly_payment_applied=0.0,
                monthly_take_home=0.0,
                monthly_breakdown=[],
            )

        tiers_with_projection[tier_name] = TierWithProjection(
            tier=tier_name,  # type: ignore[arg-type]
            jobs=scored_jobs,
            stats=stats,
            projection=projection,
        )

    return ResultsResponse(
        high=tiers_with_projection["high"],
        mid=tiers_with_projection["mid"],
        low=tiers_with_projection["low"],
        generated_at=latest_ts,
    )
