from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Re-use the same tier values; import the already-defined enum by name to
# avoid creating a duplicate PostgreSQL type.
from app.models.job_result import TierEnum


class DebtProjection(Base):
    __tablename__ = "debt_projections"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    tier: Mapped[str] = mapped_column(TierEnum, nullable=False)
    median_salary_used: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    savings_rate_pct: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    months_to_payoff: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    total_interest_paid: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
