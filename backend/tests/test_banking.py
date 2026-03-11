import pytest
from fastapi.testclient import TestClient
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from main import app
from db.supabase_client import supabase

client = TestClient(app)

test_email = f"bankuser_{uuid.uuid4().hex[:8]}@example.com"
test_password = "SecurePassword123!"

@pytest.fixture(scope="module")
def user_data():
    return {
        "name": "Bank Test User",
        "email": test_email,
        "password": test_password,
        "age": 30,
        "monthly_income": 50000.0,
        "monthly_expenses": 20000.0,
        "primary_goal": "wealth",
    }

@pytest.fixture(scope="module")
def auth_token(user_data):
    """Fixture to register and login a user, returning the access token."""
    response = client.post("/auth/register", json=user_data)
    if response.status_code == 409:
        response = client.post("/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    assert response.status_code in [200, 201]
    return response.json().get("access_token")

@pytest.fixture(scope="module")
def banking_data():
    return {
        "account_type": "savings",
        "account_name": "Main Savings",
        "institution": "HDFC Bank",
        "account_number": "1234567890",
        "current_balance": 150000.0,
        "currency": "INR",
        "is_primary": True
    }


def test_create_banking_account(auth_token, banking_data):
    """Test creating a new banking account."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/banking-accounts/", headers=headers, json=banking_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "account_id" in data
    assert data["account_type"] == banking_data["account_type"]
    assert data["account_name"] == banking_data["account_name"]
    assert data["institution"] == banking_data["institution"]
    assert data["current_balance"] == banking_data["current_balance"]

def test_list_banking_accounts(auth_token, banking_data):
    """Test listing banking accounts for a user."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/banking-accounts/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if our created account is in the list
    found = any(acc["account_name"] == banking_data["account_name"] for acc in data)
    assert found

def test_update_banking_account(auth_token, banking_data):
    """Test updating a banking account."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First get the account ID
    accounts_resp = client.get("/banking-accounts/", headers=headers)
    account_id = accounts_resp.json()[0]["account_id"]
    
    updates = {
        "current_balance": 200000.0,
        "is_primary": False
    }
    
    response = client.put(f"/banking-accounts/{account_id}", headers=headers, json=updates)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_balance"] == updates["current_balance"]
    assert data["is_primary"] == updates["is_primary"]

def test_delete_banking_account(auth_token):
    """Test deleting a banking account."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First get the account ID
    accounts_resp = client.get("/banking-accounts/", headers=headers)
    accounts = accounts_resp.json()
    if not accounts:
        pytest.skip("No accounts found to delete.")
        
    account_id = accounts[0]["account_id"]
    
    # Delete the account
    response = client.delete(f"/banking-accounts/{account_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify it was deleted
    verify_resp = client.get("/banking-accounts/", headers=headers)
    verify_accounts = verify_resp.json()
    assert all(acc["account_id"] != account_id for acc in verify_accounts)

@pytest.fixture(scope="module", autouse=True)
def cleanup(user_data):
    """Cleanup hook to remove the test user after all tests are done."""
    yield
    supabase.table('users').delete().eq('email', user_data["email"]).execute()
