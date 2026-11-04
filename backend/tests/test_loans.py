from __future__ import annotations

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_LOAN = {
    "label": "Federal Direct Subsidized",
    "loan_type": "federal_subsidized",
    "balance": 15000.0,
    "annual_interest_rate": 0.055,
    "minimum_monthly_payment": 150.0,
}


def _register_and_token(client: TestClient, email: str) -> str:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_create_loan(client: TestClient) -> None:
    """POST /loans creates a loan and returns LoanRead."""
    token = _register_and_token(client, "create_loan@example.com")
    resp = client.post("/loans", headers=_auth_headers(token), json=_VALID_LOAN)

    assert resp.status_code == 201
    data = resp.json()
    assert data["label"] == _VALID_LOAN["label"]
    assert data["loan_type"] == _VALID_LOAN["loan_type"]
    assert data["balance"] == _VALID_LOAN["balance"]
    assert data["annual_interest_rate"] == _VALID_LOAN["annual_interest_rate"]
    assert data["minimum_monthly_payment"] == _VALID_LOAN["minimum_monthly_payment"]
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


def test_list_loans(client: TestClient) -> None:
    """GET /loans returns all loans for the current user."""
    token = _register_and_token(client, "list_loans@example.com")
    headers = _auth_headers(token)

    # No loans yet
    resp = client.get("/loans", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # Create two loans
    client.post("/loans", headers=headers, json=_VALID_LOAN)
    second_loan = {**_VALID_LOAN, "label": "Private Loan", "loan_type": "private"}
    client.post("/loans", headers=headers, json=second_loan)

    resp = client.get("/loans", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_loan(client: TestClient) -> None:
    """PUT /loans/{loan_id} updates the loan and returns the updated record."""
    token = _register_and_token(client, "update_loan@example.com")
    headers = _auth_headers(token)

    create_resp = client.post("/loans", headers=headers, json=_VALID_LOAN)
    loan_id = create_resp.json()["id"]

    resp = client.put(
        f"/loans/{loan_id}",
        headers=headers,
        json={"balance": 12000.0, "label": "Updated Label"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 12000.0
    assert data["label"] == "Updated Label"
    # Unchanged fields preserved
    assert data["loan_type"] == _VALID_LOAN["loan_type"]


def test_delete_loan(client: TestClient) -> None:
    """DELETE /loans/{loan_id} removes the loan and returns 204."""
    token = _register_and_token(client, "delete_loan@example.com")
    headers = _auth_headers(token)

    create_resp = client.post("/loans", headers=headers, json=_VALID_LOAN)
    loan_id = create_resp.json()["id"]

    resp = client.delete(f"/loans/{loan_id}", headers=headers)
    assert resp.status_code == 204

    # Confirm it's gone
    list_resp = client.get("/loans", headers=headers)
    assert list_resp.json() == []


def test_delete_other_users_loan(client: TestClient) -> None:
    """DELETE /loans/{loan_id} returns 404 when the loan belongs to another user."""
    owner_token = _register_and_token(client, "owner_loan@example.com")
    other_token = _register_and_token(client, "other_loan@example.com")

    create_resp = client.post(
        "/loans", headers=_auth_headers(owner_token), json=_VALID_LOAN
    )
    loan_id = create_resp.json()["id"]

    resp = client.delete(f"/loans/{loan_id}", headers=_auth_headers(other_token))
    assert resp.status_code == 404


def test_create_loan_invalid_type(client: TestClient) -> None:
    """POST /loans with an invalid loan_type returns 422."""
    token = _register_and_token(client, "invalid_type@example.com")
    invalid_loan = {**_VALID_LOAN, "loan_type": "credit_card"}
    resp = client.post("/loans", headers=_auth_headers(token), json=invalid_loan)
    assert resp.status_code == 422
