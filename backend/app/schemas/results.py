from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.job import NormalizedJob
from app.schemas.projection import ProjectionResult


class ScoredJob(BaseModel):
    # NormalizedJob fields (copied, not inherited, per spec)
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    source: Literal["linkedin", "handshake", "indeed", "usajobs"]
    url: str | None = None
    posted_at: datetime | None = None

    # Scoring fields
    fit_score: int
    salary_median_est: float | None = None


class TierStats(BaseModel):
    salary_min: float | None = None
    salary_max: float | None = None
    salary_median: float | None = None
    job_count: int


class JobTier(BaseModel):
    tier: Literal["high", "mid", "low"]
    jobs: list[ScoredJob]
    stats: TierStats


class TieredResults(BaseModel):
    high: JobTier
    mid: JobTier
    low: JobTier


class GenerateRequest(BaseModel):
    savings_rate_pct: float = Field(default=20.0, ge=1.0, le=100.0)
    resume_text: str | None = None


class TierWithProjection(BaseModel):
    tier: Literal["high", "mid", "low"]
    jobs: list[ScoredJob]
    stats: TierStats
    projection: ProjectionResult


class ResultsResponse(BaseModel):
    high: TierWithProjection
    mid: TierWithProjection
    low: TierWithProjection
    generated_at: datetime
