from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.student_loan import StudentLoan
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanRead, LoanUpdate

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=list[LoanRead])
def list_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StudentLoan]:
    return db.query(StudentLoan).filter(StudentLoan.user_id == current_user.id).all()


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentLoan:
    loan = StudentLoan(
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def _get_own_loan(loan_id: uuid.UUID, user: User, db: Session) -> StudentLoan:
    loan: StudentLoan | None = db.get(StudentLoan, loan_id)
    if loan is None or loan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


@router.put("/{loan_id}", response_model=LoanRead)
def update_loan(
    loan_id: uuid.UUID,
    payload: LoanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentLoan:
    loan = _get_own_loan(loan_id, current_user, db)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(loan, field, value)

    db.commit()
    db.refresh(loan)
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    loan = _get_own_loan(loan_id, current_user, db)
    db.delete(loan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
