"""Tests for the debt projection engine."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from app.schemas.loan import LoanRead
from app.services.debt_projection import compute_monthly_take_home, project_payoff


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_loan(
    balance: float,
    rate: float,
    min_payment: float,
    label: str = "Loan",
) -> LoanRead:
    """Create a minimal LoanRead for testing."""
    return LoanRead(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        label=label,
        loan_type="federal_subsidized",
        balance=balance,
        annual_interest_rate=rate,
        minimum_monthly_payment=min_payment,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# compute_monthly_take_home
# ---------------------------------------------------------------------------

def test_compute_monthly_take_home_low_salary():
    """$30,000/year — matches hand-computed expected value within $5."""
    # taxable = 30000 - 14600 = 15400
    # federal = 10%*11600 + 12%*3800 = 1160 + 456 = 1616
    # FICA SS = 30000 * 0.062 = 1860
    # FICA Medicare = 30000 * 0.0145 = 435
    # annual take-home = 30000 - 1616 - 1860 - 435 = 26089
    # monthly = 26089 / 12 ≈ 2174.08
    #
    # Note: the spec states 2194 but its intermediate arithmetic uses 12% on
    # $1800 (error in spec — 15400 - 11600 = 3800, not 1800).  We assert
    # within $5 of the *correct* computed value to validate our bracket logic.
    result = compute_monthly_take_home(30_000.0)

    # Hand-computed: taxable=15400, fed=1616, ss=1860, med=435 → monthly≈2174.08
    assert abs(result - 2174.08) < 5.0, f"Expected ~2174, got {result:.2f}"


def test_compute_monthly_take_home_mid_salary():
    """$75,000/year — validates three-bracket calculation."""
    # taxable = 75000 - 14600 = 60400
    # 10% on 11600            = 1160.00
    # 12% on (47150-11600)    = 12% * 35550 = 4266.00
    # 22% on (60400-47150)    = 22% * 13250 = 2915.00
    # federal = 8341.00
    # FICA SS  = 75000 * 0.062  = 4650.00
    # FICA Med = 75000 * 0.0145 = 1087.50
    # annual take-home = 75000 - 8341 - 4650 - 1087.50 = 60921.50
    # monthly = 60921.50 / 12 ≈ 5076.79
    result = compute_monthly_take_home(75_000.0)
    assert abs(result - 5076.79) < 10.0, f"Expected ~5076.79, got {result:.2f}"


# ---------------------------------------------------------------------------
# project_payoff
# ---------------------------------------------------------------------------

def test_project_payoff_simple():
    """Single loan: $10k at 5%, $100 min; $60k salary at 30% savings.

    At $60k the monthly take-home is ~$4,183.  30% of that is ~$1,255/month
    toward the loan, so a $10k balance at 5% APR clears in roughly 9 months
    (the spec's 18-24 bound assumed a smaller payment).  We assert the correct
    computed range.
    """
    loan = _make_loan(balance=10_000.0, rate=0.05, min_payment=100.0)
    result = project_payoff([loan], annual_salary=60_000.0, savings_rate_pct=30.0)

    assert 5 <= result.months_to_payoff <= 15, (
        f"Expected 5–15 months, got {result.months_to_payoff}"
    )
    assert 0.0 <= result.total_interest_paid <= 300.0, (
        f"Expected interest $0–$300, got {result.total_interest_paid:.2f}"
    )


def test_project_payoff_avalanche_order():
    """Higher-rate loan (A) should reach zero before lower-rate loan (B)."""
    loan_a = _make_loan(balance=5_000.0, rate=0.10, min_payment=50.0, label="Loan A")
    loan_b = _make_loan(balance=5_000.0, rate=0.05, min_payment=50.0, label="Loan B")

    result = project_payoff(
        [loan_a, loan_b],
        annual_salary=80_000.0,
        savings_rate_pct=25.0,
    )

    # Find the first month where Loan A hits zero.
    loan_a_zero_month: int | None = None
    for snap in result.monthly_breakdown:
        if snap.loan_balances.get("Loan A", 1.0) == 0.0:
            loan_a_zero_month = snap.month
            break

    # Find the first month where Loan B hits zero.
    loan_b_zero_month: int | None = None
    for snap in result.monthly_breakdown:
        if snap.loan_balances.get("Loan B", 1.0) == 0.0:
            loan_b_zero_month = snap.month
            break

    assert loan_a_zero_month is not None, "Loan A never reached zero"
    assert loan_b_zero_month is not None, "Loan B never reached zero"
    assert loan_a_zero_month < loan_b_zero_month, (
        f"Expected Loan A (10%) to pay off before Loan B (5%), "
        f"but A zeroed at month {loan_a_zero_month}, B at {loan_b_zero_month}"
    )


def test_project_payoff_caps_at_600_months():
    """Unpayable loan caps the simulation at 600 months."""
    # Monthly payment ≈ $10k * 5% → ~$41.67 of interest per month alone.
    # At 5% savings on $10k salary the monthly payment is tiny.
    loan = _make_loan(balance=100_000.0, rate=0.10, min_payment=1.0)
    result = project_payoff([loan], annual_salary=10_000.0, savings_rate_pct=5.0)

    assert result.months_to_payoff == 600, (
        f"Expected cap at 600 months, got {result.months_to_payoff}"
    )


# ---------------------------------------------------------------------------
# Endpoint integration test
# ---------------------------------------------------------------------------

def test_projections_endpoint(client):
    """Register user, create loan, POST /projections/calculate → 200."""
    # Register
    reg = client.post(
        "/auth/register",
        json={"email": "proj@example.com", "password": "Secret123!"},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a loan
    loan_payload = {
        "label": "Federal Direct",
        "loan_type": "federal_subsidized",
        "balance": 15000.0,
        "annual_interest_rate": 0.05,
        "minimum_monthly_payment": 150.0,
    }
    loan_resp = client.post("/loans", json=loan_payload, headers=headers)
    assert loan_resp.status_code == 201, loan_resp.text

    # Run projection
    proj_resp = client.post(
        "/projections/calculate",
        json={"annual_salary": 60000.0, "savings_rate_pct": 20.0},
        headers=headers,
    )
    assert proj_resp.status_code == 200, proj_resp.text
    data = proj_resp.json()
    assert data["months_to_payoff"] > 0
    assert data["total_interest_paid"] >= 0
    assert data["monthly_take_home"] > 0
