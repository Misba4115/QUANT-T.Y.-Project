"""
Phase 3 Goals CRUD — pytest test suite
Covers all checklist items:
  - GET /goals/ returns empty array for new user
  - POST /goals/ creates retirement goal
  - POST /goals/ creates house purchase goal
  - GET /goals/ returns created goals
  - PUT /goals/{id} updates target_amount
  - PUT /goals/{id} updates current_saved
  - DELETE /goals/{id} removes goal
  - Cannot access another user's goals
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

def _register_and_login(suffix: str = "") -> str:
    """Register a fresh user and return their token."""
    email = f"goals_{uuid.uuid4().hex[:8]}{suffix}@example.com"
    body = {
        "name": f"Goals User {suffix}",
        "email": email,
        "password": "SecurePassword123!",
        "age": 28,
        "monthly_income": 80000.0,
        "monthly_expenses": 30000.0,
        "primary_goal": "retirement",
    }
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"], email


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def primary_token_and_email():
    token, email = _register_and_login("_primary")
    yield token, email
    supabase.table("users").delete().eq("email", email).execute()


@pytest.fixture(scope="module")
def other_token_and_email():
    """Second user used for cross-user isolation test."""
    token, email = _register_and_login("_other")
    yield token, email
    supabase.table("users").delete().eq("email", email).execute()


@pytest.fixture(scope="module")
def primary_headers(primary_token_and_email):
    token, _ = primary_token_and_email
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def other_headers(other_token_and_email):
    token, _ = other_token_and_email
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_empty_goals_for_new_user(primary_headers):
    """GET /goals/ returns empty array for new user."""
    resp = client.get("/goals/", headers=primary_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_retirement_goal(primary_headers):
    """POST /goals/ creates a retirement goal."""
    body = {
        "goal_name": "Retirement Fund",
        "goal_type": "retirement",
        "target_amount": 10000000.0,
        "current_saved": 500000.0,
        "target_date": "2045-01-01",
    }
    resp = client.post("/goals/", headers=primary_headers, json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "goal_id" in data
    assert data["goal_name"] == "Retirement Fund"
    assert data["goal_type"] == "retirement"


def test_create_house_goal(primary_headers):
    """POST /goals/ creates a house purchase goal."""
    body = {
        "goal_name": "Dream House",
        "goal_type": "house",
        "target_amount": 5000000.0,
        "current_saved": 200000.0,
        "target_date": "2030-06-01",
    }
    resp = client.post("/goals/", headers=primary_headers, json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["goal_name"] == "Dream House"
    assert data["goal_type"] == "house"


def test_list_goals_returns_created(primary_headers):
    """GET /goals/ returns both created goals."""
    resp = client.get("/goals/", headers=primary_headers)
    assert resp.status_code == 200
    goals = resp.json()
    assert len(goals) >= 2
    names = {g["goal_name"] for g in goals}
    assert "Retirement Fund" in names
    assert "Dream House" in names


def test_update_goal_target_amount(primary_headers):
    """PUT /goals/{id} updates target_amount."""
    goals = client.get("/goals/", headers=primary_headers).json()
    retirement = next(g for g in goals if g["goal_name"] == "Retirement Fund")
    goal_id = retirement["goal_id"]

    resp = client.put(
        f"/goals/{goal_id}",
        headers=primary_headers,
        json={"target_amount": 12000000.0},
    )
    assert resp.status_code == 200
    assert resp.json()["target_amount"] == 12000000.0


def test_update_goal_current_saved(primary_headers):
    """PUT /goals/{id} updates current_saved."""
    goals = client.get("/goals/", headers=primary_headers).json()
    house = next(g for g in goals if g["goal_name"] == "Dream House")
    goal_id = house["goal_id"]

    resp = client.put(
        f"/goals/{goal_id}",
        headers=primary_headers,
        json={"current_saved": 750000.0},
    )
    assert resp.status_code == 200
    assert resp.json()["current_saved"] == 750000.0


def test_delete_goal(primary_headers):
    """DELETE /goals/{id} removes the goal."""
    goals = client.get("/goals/", headers=primary_headers).json()
    house = next(g for g in goals if g["goal_name"] == "Dream House")
    goal_id = house["goal_id"]

    resp = client.delete(f"/goals/{goal_id}", headers=primary_headers)
    assert resp.status_code == 204

    remaining = client.get("/goals/", headers=primary_headers).json()
    assert all(g["goal_id"] != goal_id for g in remaining)


def test_cannot_access_other_users_goals(primary_headers, other_headers):
    """User B cannot update or delete User A's goals."""
    # Get the primary user's remaining goal
    goals = client.get("/goals/", headers=primary_headers).json()
    assert goals, "Primary user should have at least the retirement goal."
    goal_id = goals[0]["goal_id"]

    # Attempt to update with other user's token → should return 404
    resp = client.put(
        f"/goals/{goal_id}",
        headers=other_headers,
        json={"target_amount": 999.0},
    )
    assert resp.status_code == 404

    # Attempt to delete with other user's token → should return 404
    resp = client.delete(f"/goals/{goal_id}", headers=other_headers)
    assert resp.status_code == 404
