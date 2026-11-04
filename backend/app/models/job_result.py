from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

TierEnum = Enum("high", "mid", "low", name="tier_enum")

JobSourceEnum = Enum(
    "linkedin", "handshake", "indeed", "usajobs", name="job_source_enum"
)


class JobResult(Base):
    __tablename__ = "job_results"

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
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    salary_max: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    salary_median_est: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    source: Mapped[str] = mapped_column(JobSourceEnum, nullable=False)
    job_url: Mapped[str | None] = mapped_column(String, nullable=True)
    fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
