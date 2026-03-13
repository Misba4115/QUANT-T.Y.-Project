import pytest
from fastapi.testclient import TestClient
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from main import app
from db.supabase_client import supabase

client = TestClient(app)

# reuse the banking test fixtures by copying logic here

@pytest.fixture(scope="module")
def user_data():
    return {
        "name": "Chat Test User",
        "email": f"chatuser_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Password123!",
        "age": 28,
        "monthly_income": 60000.0,
        "monthly_expenses": 15000.0,
        "primary_goal": "wealth",
    }

@pytest.fixture(scope="module")
def auth_token(user_data):
    response = client.post("/auth/register", json=user_data)
    if response.status_code == 409:
        response = client.post("/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    assert response.status_code in [200, 201]
    return response.json().get("access_token")

@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    # stub the llm_service to avoid real API calls
    from services import llm_service

    monkeypatch.setattr(
        llm_service,
        "generate_chat_response",
        lambda messages: "This is a mocked reply."
    )
    yield


def test_chat_endpoint(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # initial message
    resp1 = client.post("/chat/", headers=headers, json={"message": "Hello"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "reply" in data1
    assert data1["reply"] == "This is a mocked reply."
    assert "conversation_id" in data1

    conv_id = data1["conversation_id"]

    # send another message in same conversation
    resp2 = client.post("/chat/", headers=headers, json={"message": "How are you?", "conversation_id": conv_id})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["conversation_id"] == conv_id
    assert data2["reply"] == "This is a mocked reply."

@pytest.fixture(scope="module", autouse=True)
def cleanup(user_data):
    """Remove test user (conversations/messages left behind can be purged separately)."""
    yield
    supabase.table('users').delete().eq('email', user_data["email"]).execute()
    supabase.table('chat_conversations').delete().eq('user_id', user_data["email"]).execute()
    # messages will cascade if DB foreign keys are set, otherwise purge manually later
