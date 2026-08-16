from __future__ import annotations

from datetime import date, timedelta

import numpy as np
from fastapi.testclient import TestClient

from main import app
from services.portfolio_analytics import PortfolioAnalyticsService, markowitz_analysis, snapshot_metrics


def _prices(observations: int = 90) -> tuple[np.ndarray, np.ndarray]:
    steps = np.arange(observations, dtype=float)
    first = 100 * np.exp(0.0008 * steps + 0.006 * np.sin(steps / 4))
    second = 100 * np.exp(0.00035 * steps + 0.004 * np.cos(steps / 5))
    benchmark = 100 * np.exp(0.00055 * steps + 0.005 * np.sin(steps / 6))
    return np.column_stack([first, second]), benchmark


def test_snapshot_metrics_are_observed_not_stubbed():
    start = date(2026, 1, 1)
    snapshots = [
        {"snapshot_date": (start + timedelta(days=index)).isoformat(), "net_worth": 100_000 + index * 500}
        for index in range(40)
    ]
    result = snapshot_metrics(snapshots)
    assert result["growth_percent"] == 19.5
    assert result["risk"]["status"] == "available"
    assert result["risk"]["sample_count"] == 39
    assert result["risk"]["volatility"] is not None
    assert result["risk"]["sample_period"]["from"] == "2026-01-01"


def test_markowitz_returns_current_portfolio_beta_and_actionable_weights():
    prices, benchmark = _prices()
    result = markowitz_analysis(
        ["Equity:AAA", "Equity:BBB"], prices,
        {"Equity:AAA": 0.25, "Equity:BBB": 0.75}, benchmark,
    )
    assert result["status"] == "available"
    assert result["beta_status"] == "available"
    assert result["beta_basis"] == "current_portfolio_weights"
    assert result["portfolio_beta"] is not None
    assert abs(sum(result["optimized_weights"].values()) - 1) < 1e-5
    assert result["model_version"] == "long-only-markowitz-ledoit-wolf-1.0.0"
    assert all(item["action"] in {"increase", "decrease"} for item in result["rebalancing_suggestions"])


def test_portfolio_service_uses_user_scoped_persisted_history(fake_db):
    user_id = "user-1"
    fake_db.table("equity_holdings").insert([
        {"user_id": user_id, "symbol": "AAA", "quantity": 25, "current_price": 100},
        {"user_id": user_id, "symbol": "BBB", "quantity": 75, "current_price": 100},
    ]).execute()
    prices, benchmark = _prices()
    start = date(2026, 1, 1)
    history = []
    for index, day in enumerate(start + timedelta(days=value) for value in range(len(prices))):
        for column, symbol in enumerate(("AAA", "BBB")):
            history.append({
                "user_id": user_id, "asset_type": "Equity", "instrument_key": symbol,
                "price_date": day.isoformat(), "adjusted_close": float(prices[index, column]),
                "provider": "fixture",
            })
        history.append({
            "user_id": user_id, "asset_type": "Benchmark", "instrument_key": "NIFTY50",
            "price_date": day.isoformat(), "adjusted_close": float(benchmark[index]),
            "provider": "fixture",
        })
    fake_db.table("market_price_history").insert(history).execute()
    result = PortfolioAnalyticsService(fake_db).analyze(user_id)
    assert result["status"] == "available"
    assert result["portfolio_beta"] is not None
    assert set(result["optimized_weights"]) == {"Equity:AAA", "Equity:BBB"}


def test_dashboard_uses_snapshot_risk_and_explicit_80c_evidence(fake_db):
    client = TestClient(app)
    registration = client.post("/api/auth/register", json={
        "name": "Analytics User", "email": "analytics@example.com", "password": "SecurePassword123!",
        "age": 30, "monthly_income": 100_000, "monthly_expenses": 40_000,
        "primary_goal": "wealth", "risk_profile": "moderate",
    })
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    user_id = fake_db.tables["users"][0]["user_id"]
    start = date.today() - timedelta(days=39)
    fake_db.table("portfolio_snapshots").insert([
        {"user_id": user_id, "snapshot_date": (start + timedelta(days=index)).isoformat(), "net_worth": 100_000 + index * 500}
        for index in range(40)
    ]).execute()
    fake_db.table("bank_transactions").insert({
        "user_id": user_id, "tx_date": date.today().isoformat(), "description": "PPF contribution",
        "amount": 50_000, "tx_type": "debit", "category": "PPF",
    }).execute()
    response = client.post("/api/dashboard/generate", headers=headers, json={"widgets": [], "time_period": "1y"})
    assert response.status_code == 200
    dashboard = response.json()["result"]
    assert dashboard["net_worth_growth"] == 19.5
    assert dashboard["measured_portfolio_risk"]["status"] == "available"
    assert dashboard["risk_level"] in {"Low", "Medium", "High"}
    assert dashboard["tax_saved"] == 50_000
    assert dashboard["tax_status"] == "available"
