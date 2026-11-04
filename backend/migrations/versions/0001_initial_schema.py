"""Initial schema — create all tables.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Custom enum types
    # ------------------------------------------------------------------
    experience_level_enum = postgresql.ENUM(
        "entry", "mid", "senior",
        name="experience_level_enum",
        create_type=False,
    )
    loan_type_enum = postgresql.ENUM(
        "federal_subsidized", "federal_unsubsidized", "federal_grad_plus", "private",
        name="loan_type_enum",
        create_type=False,
    )
    tier_enum = postgresql.ENUM(
        "high", "mid", "low",
        name="tier_enum",
        create_type=False,
    )
    job_source_enum = postgresql.ENUM(
        "linkedin", "handshake", "indeed", "usajobs",
        name="job_source_enum",
        create_type=False,
    )

    experience_level_enum.create(op.get_bind(), checkfirst=True)
    loan_type_enum.create(op.get_bind(), checkfirst=True)
    tier_enum.create(op.get_bind(), checkfirst=True)
    job_source_enum.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # profiles
    # ------------------------------------------------------------------
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("major", sa.String(), nullable=False),
        sa.Column(
            "interests",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "skills",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "experience_level",
            sa.Enum("entry", "mid", "senior", name="experience_level_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("savings", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ------------------------------------------------------------------
    # student_loans
    # ------------------------------------------------------------------
    op.create_table(
        "student_loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column(
            "loan_type",
            sa.Enum(
                "federal_subsidized",
                "federal_unsubsidized",
                "federal_grad_plus",
                "private",
                name="loan_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("annual_interest_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("minimum_monthly_payment", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ------------------------------------------------------------------
    # job_results
    # ------------------------------------------------------------------
    op.create_table(
        "job_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "tier",
            sa.Enum("high", "mid", "low", name="tier_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("job_title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_median_est", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "linkedin", "handshake", "indeed", "usajobs",
                name="job_source_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("job_url", sa.String(), nullable=True),
        sa.Column("fit_score", sa.Integer(), nullable=True),
    )

    # ------------------------------------------------------------------
    # debt_projections
    # ------------------------------------------------------------------
    op.create_table(
        "debt_projections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "tier",
            sa.Enum("high", "mid", "low", name="tier_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("median_salary_used", sa.Numeric(12, 2), nullable=True),
        sa.Column("savings_rate_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("months_to_payoff", sa.Integer(), nullable=True),
        sa.Column("total_interest_paid", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("debt_projections")
    op.drop_table("job_results")
    op.drop_table("student_loans")
    op.drop_table("profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS job_source_enum")
    op.execute("DROP TYPE IF EXISTS tier_enum")
    op.execute("DROP TYPE IF EXISTS loan_type_enum")
    op.execute("DROP TYPE IF EXISTS experience_level_enum")
