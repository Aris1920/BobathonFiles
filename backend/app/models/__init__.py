"""SQLAlchemy ORM models package.

Importing this package ensures all models are registered with Base.metadata
so that Alembic autogenerate can discover them.
"""

from app.models.base import Base
from app.models.debt_projection import DebtProjection
from app.models.job_result import JobResult
from app.models.profile import Profile
from app.models.student_loan import StudentLoan
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Profile",
    "StudentLoan",
    "JobResult",
    "DebtProjection",
]
