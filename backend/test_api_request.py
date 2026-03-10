import requests
import json

BASE_URL = "http://localhost:8001"

# Test registration
print("Testing /auth/register...")
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "name": "API Test User",
        "email": "apitest@example.com",
        "password": "password123",
        "phone": "+919876543210",
        "age": 25,
        "monthly_income": 50000,
        "monthly_expenses": 30000,
        "primary_goal": "Investment",
        "risk_profile": "moderate"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 201:
    print("\n✅ Registration SUCCESS!")
    access_token = response.json()["access_token"]
    
    # Test /auth/me endpoint
    print("\nTesting /auth/me...")
    me_response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"Status Code: {me_response.status_code}")
    print(f"User Data: {json.dumps(me_response.json(), indent=2)}")
else:
    print(f"\n❌ Registration FAILED")
    print(f"Error: {response.text}")