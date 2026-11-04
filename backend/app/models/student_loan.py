from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

LoanTypeEnum = Enum(
    "federal_subsidized",
    "federal_unsubsidized",
    "federal_grad_plus",
    "private",
    name="loan_type_enum",
)


class StudentLoan(Base):
    __tablename__ = "student_loans"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    loan_type: Mapped[str] = mapped_column(LoanTypeEnum, nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    annual_interest_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False
    )
    minimum_monthly_payment: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
