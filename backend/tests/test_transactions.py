"""
Phase 5 Transactions CRUD — pytest test suite
Covers:
  - Create debit transaction (Food)
  - Create credit transaction (Salary)
  - List transactions ordered by date (newest first)
  - Delete transaction
  - Unsupported asset types return 400
"""
import pytest
from fastapi.testclient import TestClient
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from main import app
from db.supabase_client import supabase

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(suffix="") -> tuple:
    email = f"tx_{uuid.uuid4().hex[:8]}{suffix}@example.com"
    body = {
        "name": "Transactions Test User",
        "email": email,
        "password": "SecurePassword123!",
        "age": 30,
        "monthly_income": 75000.0,
        "monthly_expenses": 30000.0,
        "primary_goal": "wealth",
    }
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"], email


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def primary():
    token, email = _register()
    yield {"headers": {"Authorization": f"Bearer {token}"}}
    supabase.table("users").delete().eq("email", email).execute()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_empty_transactions_list(primary):
    """GET /transactions/bank returns empty list for new user."""
    resp = client.get("/transactions/bank", headers=primary["headers"])
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_debit_transaction_food(primary):
    """Create a debit transaction categorised as Food."""
    body = {
        "tx_date": "2024-01-15",
        "description": "Swiggy Food Order",
        "amount": 450.0,
        "tx_type": "debit",
        "category": "Food",
    }
    resp = client.post("/transactions/bank", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "bank_tx_id" in data
    assert data["tx_type"] == "debit"
    assert data["category"] == "Food"
    assert data["amount"] == 450.0


def test_create_credit_transaction_salary(primary):
    """Create a credit transaction categorised as Salary."""
    body = {
        "tx_date": "2024-01-01",
        "description": "Monthly Salary - January 2024",
        "amount": 75000.0,
        "tx_type": "credit",
        "category": "Salary",
    }
    resp = client.post("/transactions/bank", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["tx_type"] == "credit"
    assert data["category"] == "Salary"
    assert data["amount"] == 75000.0


def test_list_transactions_ordered_by_date(primary):
    """GET /transactions/bank returns transactions newest first."""
    resp = client.get("/transactions/bank", headers=primary["headers"])
    assert resp.status_code == 200
    txs = resp.json()

    # Should have at least the 2 we created above
    assert len(txs) >= 2

    # Verify ordering: dates should be descending (newest first)
    dates = [t["tx_date"] for t in txs]
    assert dates == sorted(dates, reverse=True), f"Expected descending order, got: {dates}"

    # Verify both types are present
    types = {t["tx_type"] for t in txs}
    assert "debit" in types
    assert "credit" in types


def test_delete_transaction(primary):
    """DELETE /transactions/bank/{bank_tx_id} removes the transaction."""
    txs = client.get("/transactions/bank", headers=primary["headers"]).json()
    bank_tx_id = txs[0]["bank_tx_id"]  # delete the first (newest)

    resp = client.delete(f"/transactions/bank/{bank_tx_id}", headers=primary["headers"])
    assert resp.status_code == 204

    # Confirm deletion
    remaining = client.get("/transactions/bank", headers=primary["headers"]).json()
    assert all(t["bank_tx_id"] != bank_tx_id for t in remaining)


def test_unsupported_asset_type_get(primary):
    """GET /transactions/equity returns 400 — not yet implemented."""
    resp = client.get("/transactions/equity", headers=primary["headers"])
    assert resp.status_code == 400
    assert "not yet implemented" in resp.json()["detail"]


def test_unsupported_asset_type_post(primary):
    """POST /transactions/mf returns 400 — not yet implemented."""
    resp = client.post("/transactions/mf", headers=primary["headers"], json={})
    assert resp.status_code == 400


def test_unsupported_asset_type_delete(primary):
    """DELETE /transactions/crypto/{id} returns 400 — not yet implemented."""
    resp = client.delete("/transactions/crypto/fake-id", headers=primary["headers"])
    assert resp.status_code == 400


def test_invalid_tx_type_rejected(primary):
    """tx_type must be 'debit' or 'credit' — anything else returns 422."""
    body = {
        "tx_date": "2024-01-20",
        "description": "Bad tx",
        "amount": 100.0,
        "tx_type": "transfer",   # invalid
    }
    resp = client.post("/transactions/bank", headers=primary["headers"], json=body)
    assert resp.status_code == 422
