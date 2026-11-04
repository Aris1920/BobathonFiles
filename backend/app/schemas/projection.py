from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MonthSnapshot(BaseModel):
    month: int
    loan_balances: dict[str, float]
    total_remaining: float


class ProjectionResult(BaseModel):
    months_to_payoff: int
    total_interest_paid: float
    monthly_payment_applied: float
    monthly_take_home: float
    monthly_breakdown: list[MonthSnapshot]


class ProjectionRequest(BaseModel):
    annual_salary: float
    savings_rate_pct: float = Field(default=20.0, ge=1.0, le=100.0)


class ProjectionResponse(BaseModel):
    high: ProjectionResult
    mid: ProjectionResult
    low: ProjectionResult
    salaries_used: dict[str, float]


class SavedProjectionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    tier: str
    median_salary_used: float | None
    savings_rate_pct: float | None
    months_to_payoff: int | None
    total_interest_paid: float | None
