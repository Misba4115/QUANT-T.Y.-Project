from datetime import datetime, timezone

from fastapi.testclient import TestClient

from main import app
from services.market_data.models import PriceQuote
from services.market_data.service import MarketDataService


class StaticProvider:
    name = "fixture"

    def __init__(self, price: float | None, *, error: str | None = None):
        self.price = price
        self.error = error

    def fetch(self, instrument_key: str, **metadata) -> PriceQuote:
        now = datetime.now(timezone.utc)
        return PriceQuote(
            metadata.get("asset_type", "Equity"), instrument_key, self.price, "INR", self.name,
            now if self.price is not None else None, now,
            "delayed" if self.price is not None else "unavailable", self.error,
        )


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Dashboard User", "email": email, "password": "SecurePassword123!",
            "age": 32, "monthly_income": 90000, "monthly_expenses": 40000,
            "primary_goal": "wealth", "risk_profile": "aggressive",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _providers(equity: StaticProvider) -> dict:
    return {
        "Equity": equity,
        "ETF": StaticProvider(None),
        "Mutual Fund": StaticProvider(None),
        "Crypto": StaticProvider(None),
    }


def test_price_refresh_persists_provenance_and_dashboard_is_deterministic(fake_db):
    client = TestClient(app)
    headers = _register(client, "dashboard@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    client.post(
        "/api/banking-accounts/", headers=headers,
        json={"account_type": "savings", "account_name": "Cash", "institution": "Bank", "current_balance": 10000},
    )
    holding = client.post(
        "/api/holdings/equity", headers=headers,
        json={"symbol": "INFY", "equity_name": "Infosys", "exchange": "NSE", "quantity": 10, "avg_price": 1000},
    )
    assert holding.status_code == 201, holding.text

    sync = MarketDataService(fake_db, _providers(StaticProvider(1200))).refresh_user(user_id)
    assert sync["status"] == "completed"
    assert sync["updated_count"] == 1
    stored = fake_db.tables["equity_holdings"][0]
    assert stored["current_price"] == 1200
    assert stored["current_value"] == 12000
    assert stored["price_source"] == "fixture"
    assert stored["last_synced_at"]

    first = client.post("/api/dashboard/generate", headers=headers, json={"widgets": [], "time_period": "1y"})
    second = client.post("/api/dashboard/generate", headers=headers, json={"widgets": [], "time_period": "1y"})
    assert first.status_code == second.status_code == 200
    a, b = first.json()["result"], second.json()["result"]
    assert a["net_worth"] == b["net_worth"] == 22000
    assert a["portfolio_history"] == b["portfolio_history"]
    assert len(a["portfolio_history"]) == 1
    assert a["portfolio_history"][0]["value"] == 22000
    assert a["history_status"] == "available"
    assert a["measured_portfolio_risk"]["status"] == "insufficient_history"
    assert a["stated_risk_profile"] == "aggressive"
    assert a["risk_level"] == "Unavailable"
    assert a["top_holdings"][0]["valuation_status"] == "stored"


def test_failed_provider_uses_labeled_stale_cache(fake_db):
    client = TestClient(app)
    headers = _register(client, "stale@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    client.post(
        "/api/holdings/equity", headers=headers,
        json={"symbol": "TCS", "equity_name": "TCS", "exchange": "NSE", "quantity": 2, "avg_price": 3000},
    )
    fake_db.table("market_price_cache").insert(
        {
            "asset_type": "Equity", "instrument_key": "TCS", "price": 3500,
            "currency": "INR", "provider": "last_good_provider",
            "source_timestamp": "2026-08-10T10:00:00+00:00",
            "fetched_at": "2026-08-10T10:01:00+00:00", "status": "stored",
        }
    ).execute()
    result = MarketDataService(fake_db, _providers(StaticProvider(None, error="offline"))).refresh_user(user_id)
    assert result["status"] == "completed"
    assert result["quotes"][0]["status"] == "stale"
    assert result["quotes"][0]["provider"] == "last_good_provider"
    holding = fake_db.tables["equity_holdings"][0]
    assert holding["current_price"] == 3500
    assert holding["current_value"] == 7000
