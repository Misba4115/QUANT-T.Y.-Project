"""
Phase 4 Holdings CRUD — pytest test suite
Covers:
  - Equity: list, create, delete + cross-user isolation
  - Mutual Fund: list, create, delete
  - ETF: list, create, delete
  - Crypto: list, create, delete
  - CSV upload parse-only (equity)
  - CAS upload parse-only (MF)
"""
import io
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

def _register(suffix="") -> tuple[str, str]:
    email = f"hold_{uuid.uuid4().hex[:8]}{suffix}@example.com"
    body = {
        "name": "Holdings Test User",
        "email": email,
        "password": "SecurePassword123!",
        "age": 27,
        "monthly_income": 90000.0,
        "monthly_expenses": 35000.0,
        "primary_goal": "wealth",
    }
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"], email

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def primary(request):
    token, email = _register("_primary")
    yield {"token": token, "headers": {"Authorization": f"Bearer {token}"}}
    supabase.table("users").delete().eq("email", email).execute()

@pytest.fixture(scope="module")
def other(request):
    token, email = _register("_other")
    yield {"headers": {"Authorization": f"Bearer {token}"}}
    supabase.table("users").delete().eq("email", email).execute()

# ── Equity ────────────────────────────────────────────────────────────────────

def test_equity_empty_list(primary):
    resp = client.get("/holdings/equity", headers=primary["headers"])
    assert resp.status_code == 200
    assert resp.json() == []

def test_equity_create(primary):
    body = {
        "symbol": "HDFCBANK",
        "equity_name": "HDFC Bank Ltd",
        "exchange": "NSE",
        "quantity": 10.0,
        "avg_price": 1700.0,
        "broker": "Zerodha",
    }
    resp = client.post("/holdings/equity", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "equity_holding_id" in data
    assert data["symbol"] == "HDFCBANK"

def test_equity_list_has_holding(primary):
    resp = client.get("/holdings/equity", headers=primary["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

def test_equity_delete(primary):
    holdings = client.get("/holdings/equity", headers=primary["headers"]).json()
    hid = holdings[0]["equity_holding_id"]
    resp = client.delete(f"/holdings/equity/{hid}", headers=primary["headers"])
    assert resp.status_code == 204
    remaining = client.get("/holdings/equity", headers=primary["headers"]).json()
    assert all(h["equity_holding_id"] != hid for h in remaining)

def test_equity_cross_user_delete_blocked(primary, other):
    """Other user cannot delete primary user's holdings."""
    # Create a holding for primary
    body = {"symbol": "TCS", "equity_name": "Tata Consultancy Services", "exchange": "NSE",
            "quantity": 5.0, "avg_price": 3500.0}
    create_resp = client.post("/holdings/equity", headers=primary["headers"], json=body)
    hid = create_resp.json()["equity_holding_id"]
    # Other user tries to delete it
    resp = client.delete(f"/holdings/equity/{hid}", headers=other["headers"])
    assert resp.status_code == 404
    # Cleanup: primary deletes it themselves
    client.delete(f"/holdings/equity/{hid}", headers=primary["headers"])

# ── CSV Upload (parse-only) ───────────────────────────────────────────────────

def test_equity_csv_upload_preview(primary):
    csv_content = "symbol,equity_name,exchange,quantity,avg_price\nINFY,Infosys Ltd,NSE,20,1500.0\nHDFC,HDFC Bank,NSE,15,1700.0\n"
    files = {"file": ("holdings.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    resp = client.post("/holdings/equity/upload-csv", headers=primary["headers"], files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] is False
    assert data["row_count"] == 2
    assert len(data["preview"]) == 2

def test_equity_csv_upload_wrong_format(primary):
    files = {"file": ("holdings.pdf", io.BytesIO(b"not a csv"), "application/pdf")}
    resp = client.post("/holdings/equity/upload-csv", headers=primary["headers"], files=files)
    assert resp.status_code == 400

# ── Mutual Fund ───────────────────────────────────────────────────────────────

def test_mf_empty_list(primary):
    resp = client.get("/holdings/mf", headers=primary["headers"])
    assert resp.status_code == 200
    assert resp.json() == []

def test_mf_create(primary):
    body = {
        "mf_name": "SBI Bluechip Fund",
        "scheme_code": "125497",
        "fund_house": "SBI Mutual Fund",
        "category": "equity",
        "units": 100.0,
        "avg_nav": 62.5,
        "platform": "Groww",
    }
    resp = client.post("/holdings/mf", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "mf_holding_id" in data
    assert data["mf_name"] == "SBI Bluechip Fund"

def test_mf_delete(primary):
    holdings = client.get("/holdings/mf", headers=primary["headers"]).json()
    hid = holdings[0]["mf_holding_id"]
    resp = client.delete(f"/holdings/mf/{hid}", headers=primary["headers"])
    assert resp.status_code == 204

def test_mf_cas_upload_stub(primary):
    files = {"file": ("cas.pdf", io.BytesIO(b"%PDF fake content"), "application/pdf")}
    resp = client.post("/holdings/mf/upload-cas", headers=primary["headers"], files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] is False
    assert "filename" in data

# ── ETF ───────────────────────────────────────────────────────────────────────

def test_etf_empty_list(primary):
    resp = client.get("/holdings/etf", headers=primary["headers"])
    assert resp.status_code == 200
    assert resp.json() == []

def test_etf_create(primary):
    body = {
        "symbol": "NIFTYBEES",
        "etf_name": "Nippon India ETF Nifty BeES",
        "exchange": "NSE",
        "quantity": 50.0,
        "avg_price": 220.0,
        "broker": "Zerodha",
    }
    resp = client.post("/holdings/etf", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    assert "etf_holding_id" in resp.json()

def test_etf_delete(primary):
    holdings = client.get("/holdings/etf", headers=primary["headers"]).json()
    hid = holdings[0]["etf_holding_id"]
    resp = client.delete(f"/holdings/etf/{hid}", headers=primary["headers"])
    assert resp.status_code == 204

# ── Crypto ────────────────────────────────────────────────────────────────────

def test_crypto_empty_list(primary):
    resp = client.get("/holdings/crypto", headers=primary["headers"])
    assert resp.status_code == 200
    assert resp.json() == []

def test_crypto_create(primary):
    body = {
        "symbol": "BTC",
        "crypto_name": "Bitcoin",
        "network": "Bitcoin",
        "quantity": 0.05,
        "avg_price": 3500000.0,
        "exchange": "CoinDCX",
    }
    resp = client.post("/holdings/crypto", headers=primary["headers"], json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "crypto_holding_id" in data
    assert data["symbol"] == "BTC"

def test_crypto_delete(primary):
    holdings = client.get("/holdings/crypto", headers=primary["headers"]).json()
    hid = holdings[0]["crypto_holding_id"]
    resp = client.delete(f"/holdings/crypto/{hid}", headers=primary["headers"])
    assert resp.status_code == 204
