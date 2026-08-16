from fastapi.testclient import TestClient

from main import app


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "CRUD User", "email": "crud@example.com", "password": "SecurePassword123!",
            "age": 35, "monthly_income": 80000, "monthly_expenses": 30000,
            "primary_goal": "retirement", "risk_profile": "conservative",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_current_crud_surface_for_goals_and_all_holdings(fake_db):
    client = TestClient(app)
    headers = _headers(client)

    goal = client.post(
        "/api/goals/", headers=headers,
        json={"goal_name": "Home", "goal_type": "house", "target_amount": 5000000, "current_saved": 100000},
    )
    assert goal.status_code == 201, goal.text
    goal_id = goal.json()["goal_id"]
    updated = client.put(f"/api/goals/{goal_id}", headers=headers, json={"current_saved": 125000})
    assert updated.status_code == 200
    assert updated.json()["current_saved"] == 125000
    assert len(client.get("/api/goals/", headers=headers).json()) == 1
    assert client.delete(f"/api/goals/{goal_id}", headers=headers).status_code == 204

    cases = [
        (
            "equity", "equity_holding_id",
            {"symbol": "INFY", "equity_name": "Infosys", "exchange": "NSE", "quantity": 2, "avg_price": 1500},
        ),
        (
            "mf", "mf_holding_id",
            {"mf_name": "Index Fund", "scheme_code": "1001", "units": 10, "avg_nav": 100},
        ),
        (
            "etf", "etf_holding_id",
            {"symbol": "NIFTYBEES", "etf_name": "Nifty BeES", "exchange": "NSE", "quantity": 5, "avg_price": 200},
        ),
        (
            "crypto", "crypto_holding_id",
            {"symbol": "BTC", "crypto_name": "Bitcoin", "quantity": 0.01, "avg_price": 5000000},
        ),
    ]
    for route, id_field, payload in cases:
        created = client.post(f"/api/holdings/{route}", headers=headers, json=payload)
        assert created.status_code == 201, created.text
        record_id = created.json()[id_field]
        listed = client.get(f"/api/holdings/{route}", headers=headers)
        assert listed.status_code == 200
        assert [row[id_field] for row in listed.json()] == [record_id]
        assert client.delete(f"/api/holdings/{route}/{record_id}", headers=headers).status_code == 204
        assert client.get(f"/api/holdings/{route}", headers=headers).json() == []


def test_asset_transaction_routes_are_real_not_catchall_stubs(fake_db):
    client = TestClient(app)
    headers = _headers(client)
    payloads = {
        "equity": {"tx_date": "2026-01-01", "tx_type": "buy", "symbol": "INFY", "quantity": 2, "price": 1500},
        "etf": {"tx_date": "2026-01-01", "tx_type": "buy", "symbol": "NIFTYBEES", "quantity": 4, "price": 250},
        "crypto": {"tx_date": "2026-01-01", "tx_type": "buy", "symbol": "BTC", "quantity": 0.01, "price": 5000000},
        "mf": {"tx_date": "2026-01-01", "tx_type": "buy", "mf_name": "Index Fund", "scheme_code": "1001", "units": 10, "nav": 100},
    }
    id_fields = {"equity": "equity_tx_id", "etf": "etf_tx_id", "crypto": "crypto_tx_id", "mf": "mf_tx_id"}
    for route, payload in payloads.items():
        created = client.post(f"/api/transactions/{route}", headers=headers, json=payload)
        assert created.status_code == 201, created.text
        tx_id = created.json()[id_fields[route]]
        assert client.get(f"/api/transactions/{route}", headers=headers).json()[0][id_fields[route]] == tx_id
        assert client.delete(f"/api/transactions/{route}/{tx_id}", headers=headers).status_code == 204
