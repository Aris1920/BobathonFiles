"""Projections router — calculate and retrieve debt payoff projections."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.debt_projection import DebtProjection
from app.models.student_loan import StudentLoan
from app.models.user import User
from app.schemas.loan import LoanRead
from app.schemas.projection import (
    ProjectionRequest,
    ProjectionResult,
    SavedProjectionRead,
)
from app.services.debt_projection import project_payoff

router = APIRouter(prefix="/projections", tags=["projections"])


@router.post("/calculate", response_model=ProjectionResult)
def calculate_projection(
    body: ProjectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectionResult:
    """Run the avalanche payoff simulation for the current user's loans.

    Uses the salary and savings rate from the request body. Persists a
    snapshot to the DebtProjection table and returns the full result.
    """
    # Load user's loans from DB.
    db_loans = (
        db.query(StudentLoan)
        .filter(StudentLoan.user_id == current_user.id)
        .all()
    )
    loans = [LoanRead.model_validate(loan) for loan in db_loans]

    result = project_payoff(
        loans=loans,
        annual_salary=body.annual_salary,
        savings_rate_pct=body.savings_rate_pct,
    )

    # Persist a summary snapshot.
    projection = DebtProjection(
        user_id=current_user.id,
        tier="mid",  # single-salary endpoint uses "mid" as the tier label
        median_salary_used=body.annual_salary,
        savings_rate_pct=body.savings_rate_pct,
        months_to_payoff=result.months_to_payoff,
        total_interest_paid=result.total_interest_paid,
    )
    db.add(projection)
    db.commit()

    return result


@router.get("", response_model=list[SavedProjectionRead])
def list_projections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DebtProjection]:
    """Return the 20 most recent saved projections for the current user."""
    return (
        db.query(DebtProjection)
        .filter(DebtProjection.user_id == current_user.id)
        .order_by(DebtProjection.created_at.desc())
        .limit(20)
        .all()
    )
