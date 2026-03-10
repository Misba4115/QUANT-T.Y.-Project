import requests

url = "http://localhost:8001/auth/register"
payload = {
    "name": "Jane",
    "email": "jane8001@example.com",
    "password": "strongpassword123",
    "age": 25,
    "monthly_income": 5000,
    "monthly_expenses": 2000,
    "primary_goal": "Wealth"
}

try:
    response = requests.post(url, json=payload)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
except Exception as e:
    print("Request failed:", e)
