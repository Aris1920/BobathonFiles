from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    label: str | None
    loan_type: str
    balance: float
    annual_interest_rate: float
    minimum_monthly_payment: float
    created_at: datetime


class LoanCreate(BaseModel):
    label: str
    loan_type: Literal[
        "federal_subsidized",
        "federal_unsubsidized",
        "federal_grad_plus",
        "private",
    ]
    balance: float = Field(gt=0)
    annual_interest_rate: float = Field(gt=0, lt=1)
    minimum_monthly_payment: float = Field(ge=0)


class LoanUpdate(BaseModel):
    label: str | None = None
    loan_type: Literal[
        "federal_subsidized",
        "federal_unsubsidized",
        "federal_grad_plus",
        "private",
    ] | None = None
    balance: float | None = Field(default=None, gt=0)
    annual_interest_rate: float | None = Field(default=None, gt=0, lt=1)
    minimum_monthly_payment: float | None = Field(default=None, ge=0)
