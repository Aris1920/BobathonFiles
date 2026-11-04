"""Debt projection engine — avalanche payoff simulation with US 2024 tax logic."""
from __future__ import annotations

from app.schemas.loan import LoanRead
from app.schemas.projection import MonthSnapshot, ProjectionResult

# ---------------------------------------------------------------------------
# US 2024 federal income tax brackets (single filer, standard deduction
# of $14,600 already subtracted to arrive at taxable income).
# Each entry: (upper_bound_of_bracket, marginal_rate)
# The last bracket has no upper bound — use float("inf").
# ---------------------------------------------------------------------------
_BRACKETS: list[tuple[float, float]] = [
    (11_600.0, 0.10),
    (47_150.0, 0.12),
    (100_525.0, 0.22),
    (191_950.0, 0.24),
    (243_725.0, 0.32),
    (609_350.0, 0.35),
    (float("inf"), 0.37),
]

_STANDARD_DEDUCTION = 14_600.0
_SS_WAGE_BASE = 168_600.0
_SS_RATE = 0.062
_MEDICARE_RATE = 0.0145

_MAX_MONTHS = 600


def compute_monthly_take_home(annual_salary: float) -> float:
    """Return estimated monthly after-tax take-home for a US single filer (2024).

    Applies the 2024 standard deduction, federal marginal tax brackets, and
    FICA (Social Security + Medicare) on gross income.
    """
    taxable_income = max(0.0, annual_salary - _STANDARD_DEDUCTION)

    # Compute federal income tax using marginal brackets.
    federal_tax = 0.0
    previous_upper = 0.0
    for upper, rate in _BRACKETS:
        if taxable_income <= previous_upper:
            break
        taxable_in_bracket = min(taxable_income, upper) - previous_upper
        federal_tax += taxable_in_bracket * rate
        previous_upper = upper

    # FICA
    fica_ss = min(annual_salary, _SS_WAGE_BASE) * _SS_RATE
    fica_medicare = annual_salary * _MEDICARE_RATE

    annual_take_home = annual_salary - federal_tax - fica_ss - fica_medicare
    return annual_take_home / 12.0


def project_payoff(
    loans: list[LoanRead],
    annual_salary: float,
    savings_rate_pct: float,
) -> ProjectionResult:
    """Simulate month-by-month payoff using the avalanche method.

    Parameters
    ----------
    loans:
        The user's current loan records.
    annual_salary:
        Gross annual salary to use for take-home calculation.
    savings_rate_pct:
        Percentage of monthly take-home devoted to loan payments (1–100).

    Returns
    -------
    ProjectionResult
        Full breakdown capped at 600 months.
    """
    monthly_take_home = compute_monthly_take_home(annual_salary)
    monthly_payment = monthly_take_home * (savings_rate_pct / 100.0)

    # Working state — keyed by str(loan.id)
    balances: dict[str, float] = {str(loan.id): float(loan.balance) for loan in loans}
    rates: dict[str, float] = {str(loan.id): float(loan.annual_interest_rate) for loan in loans}
    minimums: dict[str, float] = {str(loan.id): float(loan.minimum_monthly_payment) for loan in loans}
    # Label for snapshot display (fall back to str id if no label set)
    labels: dict[str, str] = {
        str(loan.id): (loan.label or str(loan.id)) for loan in loans
    }

    total_interest_paid = 0.0
    monthly_breakdown: list[MonthSnapshot] = []

    for month in range(1, _MAX_MONTHS + 1):
        # ---- a. Accrue interest ----
        for lid, bal in balances.items():
            if bal > 0:
                interest = bal * (rates[lid] / 12.0)
                total_interest_paid += interest
                balances[lid] = bal + interest

        # ---- b. Apply minimum payments ----
        total_paid_this_month = 0.0
        for lid in sorted(balances.keys()):  # stable order
            if balances[lid] > 0:
                payment = min(minimums[lid], balances[lid])
                balances[lid] -= payment
                total_paid_this_month += payment

        # ---- c. Surplus toward highest-rate loan ----
        surplus = max(0.0, monthly_payment - total_paid_this_month)
        if surplus > 0:
            # Find the active loan with the highest annual rate.
            active = [(lid, rates[lid]) for lid, bal in balances.items() if bal > 0]
            if active:
                target_lid = max(active, key=lambda x: x[1])[0]
                applied = min(surplus, balances[target_lid])
                balances[target_lid] -= applied

        # ---- d. Clamp all balances to >= 0 ----
        for lid in balances:
            if balances[lid] < 0:
                balances[lid] = 0.0

        # ---- e. Record snapshot (using labels as keys) ----
        snapshot_balances = {labels[lid]: round(bal, 2) for lid, bal in balances.items()}
        total_remaining = sum(balances.values())
        if len(monthly_breakdown) < _MAX_MONTHS:
            monthly_breakdown.append(
                MonthSnapshot(
                    month=month,
                    loan_balances=snapshot_balances,
                    total_remaining=round(total_remaining, 2),
                )
            )

        # ---- f. Stop when all paid off ----
        if total_remaining == 0.0:
            break

    months_to_payoff = len(monthly_breakdown)

    return ProjectionResult(
        months_to_payoff=months_to_payoff,
        total_interest_paid=round(total_interest_paid, 2),
        monthly_payment_applied=round(monthly_payment, 2),
        monthly_take_home=round(monthly_take_home, 2),
        monthly_breakdown=monthly_breakdown,
    )
