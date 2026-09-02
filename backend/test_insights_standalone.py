"""
Standalone Insights Tab Test Script
====================================
Tests ALL layers of the insights implementation without needing the
FastAPI server or a real Supabase connection.

Covers:
  1. Price fetching from the internet (yfinance, mfapi.in, CoinGecko)
  2. Layer A — Trading Signals (EWMA forecast, rebalance actions, GC-SEC Arbiter tax check)
  3. Layer B — Investment Recommendations (goal gap, SIP calc, instrument suggestions, priority action)
  4. GC-SEC metadata (grounding summary, arbiter summary)
  5. End-to-end InsightsService.generate() with mocked DB

Run with:
    conda activate miniproject
    cd backend
    python test_insights_standalone.py
"""
from __future__ import annotations

import json
import math
import sys
import traceback
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np

# ─── Colour helpers ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"
WARN = f"{YELLOW}WARN{RESET}"

results: list[tuple[str, str, str]] = []  # (section, name, status)

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check(name: str, passed: bool, detail: str = "", warn: bool = False):
    status = WARN if warn else (PASS if passed else FAIL)
    marker = "WARN" if warn else ("PASS" if passed else "FAIL")
    results.append((_current_section, name, marker))
    suffix = f"  -> {detail}" if detail else ""
    sym = "ok" if passed else "!!"
    print(f"  [{sym}] {status}  {name}{suffix}")

_current_section = "General"
def set_section(s: str):
    global _current_section
    _current_section = s

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Price fetching from the internet
# ─────────────────────────────────────────────────────────────────────────────
section("1. LIVE PRICE FETCHING FROM INTERNET")
set_section("Price Fetching")

def test_yfinance_equity():
    try:
        import yfinance as yf
        ticker = yf.Ticker("RELIANCE.NS")
        price = float(ticker.fast_info["last_price"])
        assert price > 0, f"Got non-positive price: {price}"
        check("yfinance - NSE Equity (RELIANCE.NS)", True, f"Rs {price:,.2f}")
        return price
    except Exception as e:
        check("yfinance - NSE Equity (RELIANCE.NS)", False, str(e))
        return None

def test_yfinance_etf():
    try:
        import yfinance as yf
        ticker = yf.Ticker("NIFTYBEES.NS")
        price = float(ticker.fast_info["last_price"])
        assert price > 0
        check("yfinance - ETF (NIFTYBEES.NS)", True, f"Rs {price:,.2f}")
        return price
    except Exception as e:
        check("yfinance - ETF (NIFTYBEES.NS)", False, str(e))
        return None

def test_mfapi():
    try:
        import httpx
        with httpx.Client(timeout=15) as client:
            r = client.get("https://api.mfapi.in/mf/119598")
            r.raise_for_status()
        data = r.json()
        nav = float(data["data"][0]["nav"])
        fund_name = data.get("meta", {}).get("scheme_name", "HDFC Fund")
        assert nav > 0
        check("mfapi.in - Mutual Fund NAV", True, f"NAV Rs {nav:,.4f} ({fund_name[:40]})")
        return nav
    except Exception as e:
        check("mfapi.in - Mutual Fund NAV", False, str(e))
        return None

def test_coingecko():
    try:
        import httpx
        with httpx.Client(timeout=15) as client:
            r = client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "inr", "include_last_updated_at": "true"},
            )
            r.raise_for_status()
        price = float(r.json()["bitcoin"]["inr"])
        assert price > 0
        check("CoinGecko - BTC/INR (live)", True, f"Rs {price:,.0f}")
        return price
    except Exception as e:
        check("CoinGecko - BTC/INR (live)", False, str(e))
        return None

def test_yfinance_history():
    try:
        import yfinance as yf
        ticker = yf.Ticker("RELIANCE.NS")
        hist = ticker.history(period="1y", auto_adjust=True)
        assert not hist.empty and "Close" in hist
        closes = hist["Close"].dropna().tolist()
        assert len(closes) >= 50, f"Only got {len(closes)} data points"
        check("yfinance - Historical Close Prices (1y)", True, f"{len(closes)} trading days returned")
        return closes
    except Exception as e:
        check("yfinance - Historical Close Prices (1y)", False, str(e))
        return None

equity_price   = test_yfinance_equity()
etf_price      = test_yfinance_etf()
mf_nav         = test_mfapi()
crypto_price   = test_coingecko()
hist_closes    = test_yfinance_history()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Layer A: Trading Signal Calculations
# ─────────────────────────────────────────────────────────────────────────────
section("2. LAYER A - TRADING SIGNAL CALCULATIONS")
set_section("Layer A")

sys.path.insert(0, ".")
try:
    from services.insights_service import (
        EWMA_SPAN,
        SIGNAL_THRESHOLD,
        _build_asset_forecasts,
        _build_rebalance_actions,
        _confidence_label,
        _ewma_return,
    )
    check("Import insights_service pure functions", True)
except Exception as e:
    check("Import insights_service pure functions", False, str(e))
    print(f"\nCANNOT CONTINUE: {e}")
    sys.exit(1)

def test_ewma_on_real_data():
    if not hist_closes:
        check("EWMA return on real historical data", False, "No historical prices (test 1e failed)")
        return
    ewma = _ewma_return(hist_closes)
    assert isinstance(ewma, float)
    assert -2.0 <= ewma <= 5.0, f"Unreasonable annualised return: {ewma:.4f}"
    check("EWMA return on real historical data", True, f"{ewma*100:.2f}% annualised (RELIANCE.NS)")

test_ewma_on_real_data()

def test_confidence_labels():
    assert _confidence_label(0.10) == "High",   "Expected High for vol=0.10"
    assert _confidence_label(0.80) == "Medium",  f"Expected Medium for vol=0.80, got {_confidence_label(0.80)}"
    assert _confidence_label(1.50) == "Low",     "Expected Low for vol=1.50"
    check("Confidence label thresholds", True, "High/Medium/Low bands correct")

test_confidence_labels()

def test_build_asset_forecasts():
    holdings = {"Equity": 500_000, "Mutual Fund": 200_000, "Crypto": 50_000}
    price_history: dict[str, list[float]] = {}
    if hist_closes:
        price_history["Equity"] = hist_closes[-90:]
    price_history["Mutual Fund"] = [100.0 + i * 0.05 for i in range(60)]
    price_history["Crypto"] = [100.0 + ((-1)**i) * i * 0.3 for i in range(60)]

    pa_result = {"expected_annual_volatility": 0.20, "optimized_weights": {}}
    forecasts = _build_asset_forecasts(holdings, price_history, pa_result)

    assert isinstance(forecasts, list), "Expected a list"
    assert len(forecasts) == 3, f"Expected 3 forecasts, got {len(forecasts)}"

    for f in forecasts:
        assert "asset_class" in f
        assert "forecast_return_midpoint" in f
        assert f["confidence"] in ("High", "Medium", "Low")
        assert f["direction"] in ("up", "down", "flat")
        assert f["horizon_days"] == 30

    check("Asset forecast construction", True,
          " | ".join(f"{f['asset_class']}: {f['direction']} {f['forecast_return_midpoint']:.1f}% ({f['confidence']})" for f in forecasts))

test_build_asset_forecasts()

def test_rebalance_actions_with_tax():
    holdings = {"Equity": 600_000, "Mutual Fund": 100_000, "Debt": 50_000}
    pa_result = {"optimized_weights": {"Equity": 0.40, "Mutual Fund": 0.40, "Debt": 0.20}}
    tax_summary = {"realized_gain_breakdown": [{"stcg": 15_000, "ltcg": 0}]}
    actions = _build_rebalance_actions(holdings, pa_result, tax_summary)
    assert isinstance(actions, list)
    signals = {a["asset_class"]: a["signal"] for a in actions}
    assert signals.get("Equity") == "REDUCE", f"Expected REDUCE for Equity, got {signals.get('Equity')}"
    equity_action = next(a for a in actions if a["asset_class"] == "Equity")
    assert equity_action["tax_flag"] is not None, "Expected a STCG tax flag on Equity REDUCE"
    check("Rebalance signals (Equity overweight -> REDUCE)", True,
          " | ".join(f"{k}={v}" for k, v in signals.items()))
    check("GC-SEC Step 2 - STCG tax flag on Equity REDUCE", True,
          equity_action["tax_flag"][:60])

test_rebalance_actions_with_tax()

def test_rebalance_no_tax():
    holdings = {"Equity": 600_000, "Debt": 150_000}
    pa_result = {"optimized_weights": {}}
    tax_summary = {"realized_gain_breakdown": []}
    actions = _build_rebalance_actions(holdings, pa_result, tax_summary)
    for a in actions:
        assert a["tax_flag"] is None, f"Unexpected tax flag: {a['tax_flag']}"
    check("GC-SEC Step 2 - No tax flag when STCG=0", True)

test_rebalance_no_tax()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Layer B: Investment Recommendation Calculations
# ─────────────────────────────────────────────────────────────────────────────
section("3. LAYER B - INVESTMENT RECOMMENDATION CALCULATIONS")
set_section("Layer B")

from services.insights_service import (
    _build_instrument_suggestions,
    _build_priority_action,
    _goal_gap,
    _goal_horizon,
)

def test_goal_horizon():
    from datetime import timedelta
    today = date.today()
    short_date  = (today + timedelta(days=365)).isoformat()
    medium_date = (today + timedelta(days=365*4)).isoformat()
    long_date   = (today + timedelta(days=365*10)).isoformat()
    assert _goal_horizon(short_date) == "short"
    assert _goal_horizon(medium_date) == "medium"
    assert _goal_horizon(long_date) == "long"
    assert _goal_horizon(None) == "long"
    check("Goal horizon classification (short/medium/long/None)", True)

test_goal_horizon()

def test_goal_gap():
    goal = {
        "goal_id": "g1",
        "name": "Retirement Fund",
        "target_amount": 5_000_000,
        "current_amount": 800_000,
        "target_date": (date.today().replace(year=date.today().year + 12)).isoformat(),
    }
    gap = _goal_gap(goal, net_worth=800_000)
    assert gap["gap"] == 5_000_000 - 800_000
    assert gap["shortfall_pct"] == round((4_200_000 / 5_000_000) * 100, 1)
    assert gap["on_track"] is False
    assert gap["required_monthly_sip"] > 0
    check("Goal gap calculation",  True,
          f"Gap Rs{gap['gap']:,.0f} | Shortfall {gap['shortfall_pct']}% | SIP Rs{gap['required_monthly_sip']:,.0f}/mo")

    goal2 = {"goal_id": "g2", "name": "Emergency Fund",
              "target_amount": 100_000, "current_amount": 95_000, "target_date": None}
    gap2 = _goal_gap(goal2, net_worth=95_000)
    assert gap2["on_track"] is True
    check("Goal gap - on-track case (within 10%)", True, f"Shortfall {gap2['shortfall_pct']}%")

test_goal_gap()

def test_instrument_suggestions():
    goal_gaps = [
        {"goal_name": "Retirement", "on_track": False, "horizon": "long", "gap": 4_200_000, "shortfall_pct": 84},
        {"goal_name": "Child Education", "on_track": False, "horizon": "medium", "gap": 500_000, "shortfall_pct": 50},
    ]
    suggestions = _build_instrument_suggestions("moderate", goal_gaps, {"Equity": 500_000})
    assert len(suggestions) > 0
    check("Instrument suggestions - moderate profile", True,
          " | ".join(s["name"] for s in suggestions))

    sugg_cons = _build_instrument_suggestions("conservative", goal_gaps, {})
    check("Instrument suggestions - conservative profile", True,
          " | ".join(f"{s['name']}({s['risk_level']})" for s in sugg_cons))

    on_track_gaps = [{"goal_name": "Goal", "on_track": True, "horizon": "long", "gap": 0, "shortfall_pct": 0}]
    sugg_fallback = _build_instrument_suggestions("moderate", on_track_gaps, {"Equity": 500_000})
    assert len(sugg_fallback) > 0
    check("Fallback suggestions when all goals on track", True,
          f"{len(sugg_fallback)} fallback instruments")

test_instrument_suggestions()

def test_priority_action():
    unmet_gaps = [
        {"goal_name": "Retirement", "on_track": False, "horizon": "long",
         "gap": 4_200_000, "shortfall_pct": 84, "required_monthly_sip": 23_333},
        {"goal_name": "Car", "on_track": False, "horizon": "short",
         "gap": 200_000, "shortfall_pct": 40, "required_monthly_sip": 8_333},
    ]
    suggestions = [{"name": "Nifty Next 50 Index Fund"}]
    action = _build_priority_action(unmet_gaps, cashflow_surplus=5_000, suggestions=suggestions)
    assert action is not None
    assert action["action"] == "Increase monthly investment"
    assert "Retirement" in action["driven_by_goal"]
    check("Priority action - increase investment (surplus insufficient)", True,
          action["description"][:80])

    action2 = _build_priority_action(unmet_gaps, cashflow_surplus=30_000, suggestions=suggestions)
    assert action2["action"] == "Deploy monthly surplus"
    check("Priority action - deploy surplus (surplus adequate)", True,
          action2["description"][:80])

    no_action = _build_priority_action(
        [{"goal_name": "G", "on_track": True, "gap": 0, "shortfall_pct": 0, "required_monthly_sip": 0}],
        cashflow_surplus=10_000, suggestions=[]
    )
    assert no_action is None
    check("Priority action - None when all goals on track", True)

test_priority_action()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — GC-SEC End-to-End with mocked DB
# ─────────────────────────────────────────────────────────────────────────────
section("4. GC-SEC PIPELINE - END-TO-END with Mocked DB")
set_section("GC-SEC End-to-End")

def build_mock_db():
    db = MagicMock()
    equity_rows = [
        {"equity_holding_id": "e1", "user_id": "demo", "symbol": "RELIANCE",
         "quantity": 10, "current_price": 2800.0, "avg_price": 2500.0, "exchange": "NSE"},
        {"equity_holding_id": "e2", "user_id": "demo", "symbol": "INFY",
         "quantity": 20, "current_price": 1750.0, "avg_price": 1600.0, "exchange": "NSE"},
    ]
    mf_rows = [
        {"mf_holding_id": "m1", "user_id": "demo", "scheme_code": "119598",
         "units": 500, "current_nav": 150.0, "avg_nav": 120.0},
    ]
    crypto_rows = [
        {"crypto_holding_id": "c1", "user_id": "demo", "symbol": "BTC",
         "quantity": 0.05, "current_price": 6_500_000.0, "avg_price": 5_000_000.0},
    ]
    snapshots = [
        {"snapshot_date": f"2024-{m:02d}-01", "asset_class": "Equity",
         "value": 50_000 + m * 2_000}
        for m in range(1, 13)
    ] + [
        {"snapshot_date": f"2025-{m:02d}-01", "asset_class": "Mutual Fund",
         "value": 75_000 + m * 1_500}
        for m in range(1, 9)
    ]
    goals = [
        {"goal_id": "g1", "user_id": "demo", "name": "Retirement Fund",
         "target_amount": 5_000_000, "current_amount": 800_000, "target_date": "2040-01-01"},
        {"goal_id": "g2", "user_id": "demo", "name": "Emergency Fund",
         "target_amount": 200_000, "current_amount": 185_000, "target_date": "2026-12-01"},
    ]
    user_profile = [{"user_id": "demo", "risk_profile": "moderate",
                     "monthly_income": 120_000, "monthly_expenses": 65_000}]

    rows_map = {
        "equity_holdings": equity_rows,
        "mutual_fund_holdings": mf_rows,
        "etf_holdings": [],
        "crypto_holdings": crypto_rows,
        "portfolio_snapshots": snapshots,
        "goals": goals,
        "users": user_profile,
        "equity_transactions": [],
        "mf_transactions": [],
        "etf_transactions": [],
    }

    def table_mock(table_name):
        t = MagicMock()
        rows = rows_map.get(table_name, [])
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=rows)
        chain.eq.return_value = chain
        chain.neq.return_value = chain
        chain.limit.return_value = chain
        chain.order.return_value = chain
        chain.select.return_value = chain
        chain.gte.return_value = chain
        chain.lte.return_value = chain
        t.select.return_value = chain
        t.insert.return_value = chain
        t.update.return_value = chain
        t.upsert.return_value = chain
        return t

    db.table.side_effect = table_mock
    return db

def test_full_pipeline():
    from services.insights_service import InsightsService

    db = build_mock_db()
    service = InsightsService(db)

    try:
        result = service.generate("demo")
    except Exception as e:
        check("InsightsService.generate() completes without error", False,
              f"{type(e).__name__}: {e}")
        traceback.print_exc()
        return None

    check("InsightsService.generate() completes without error", True)

    for key in ("generated_at", "model_version", "user_context", "layer_a", "layer_b", "gc_sec"):
        check(f"Result has key '{key}'", key in result, str(result.get(key, "MISSING"))[:60])

    ctx = result.get("user_context", {})
    check("user_context.risk_profile present", bool(ctx.get("risk_profile")), ctx.get("risk_profile", "MISSING"))
    check("user_context.net_worth > 0", ctx.get("net_worth", 0) > 0, f"Rs {ctx.get('net_worth', 0):,.0f}")
    check("user_context.cashflow_surplus >= 0", ctx.get("cashflow_surplus", -1) >= 0,
          f"Rs {ctx.get('cashflow_surplus', 0):,.0f}")

    la = result.get("layer_a", {})
    check("Layer A status = 'available'", la.get("status") == "available", f"status={la.get('status')}")
    forecasts = la.get("asset_forecasts", [])
    check("Layer A - has >=1 asset forecast", len(forecasts) >= 1, f"{len(forecasts)} forecasts")
    for f in forecasts:
        check(f"  Layer A forecast [{f['asset_class']}] direction/confidence",
              f.get("direction") in ("up","down","flat") and f.get("confidence") in ("High","Medium","Low"),
              f"{f['direction']} | {f['forecast_return_midpoint']}% | {f['confidence']} conf")

    rebalances = la.get("rebalance_actions", [])
    check("Layer A - has rebalance actions", len(rebalances) >= 1,
          " | ".join(r["signal"] for r in rebalances))

    lb = result.get("layer_b", {})
    check("Layer B status = 'available'", lb.get("status") == "available", f"status={lb.get('status')}")
    goal_gaps = lb.get("goal_gaps", [])
    check("Layer B - has goal gap entries", len(goal_gaps) >= 1, f"{len(goal_gaps)} goals")
    for g in goal_gaps:
        check(f"  Layer B goal [{g['goal_name']}] gap/SIP computed",
              g.get("gap") is not None and g.get("required_monthly_sip") is not None,
              f"Gap=Rs{g.get('gap',0):,.0f} | SIP=Rs{g.get('required_monthly_sip',0):,.0f}/mo | on_track={g.get('on_track')}")

    suggestions = lb.get("instrument_suggestions", [])
    check("Layer B - has instrument suggestions", len(suggestions) >= 1,
          " | ".join(s["name"] for s in suggestions[:3]))

    priority = lb.get("priority_action")
    check("Layer B - has priority action", priority is not None,
          priority.get("action", "None") if priority else "None")

    gc = result.get("gc_sec", {})
    grounding = gc.get("grounding", {})
    check("GC-SEC grounding checks_performed > 0", grounding.get("checks_performed", 0) > 0,
          f"{grounding.get('checks_performed')} checks")
    check("GC-SEC arbiter summary present", "tax_flags_raised" in gc.get("arbiter", {}),
          f"tax_flags={gc.get('arbiter',{}).get('tax_flags_raised')}")
    check("GC-SEC disclaimer present", bool(gc.get("disclaimer")))

    return result

result = test_full_pipeline()

if result:
    section("5. RESULT JSON OUTPUT")
    print("\n-- user_context --")
    print(json.dumps(result.get("user_context"), indent=2))
    print("\n-- layer_a.asset_forecasts --")
    print(json.dumps(result.get("layer_a", {}).get("asset_forecasts"), indent=2))
    print("\n-- layer_a.rebalance_actions --")
    print(json.dumps(result.get("layer_a", {}).get("rebalance_actions"), indent=2))
    print("\n-- layer_b.goal_gaps --")
    print(json.dumps(result.get("layer_b", {}).get("goal_gaps"), indent=2))
    print("\n-- layer_b.instrument_suggestions --")
    print(json.dumps(result.get("layer_b", {}).get("instrument_suggestions"), indent=2))
    print("\n-- layer_b.priority_action --")
    print(json.dumps(result.get("layer_b", {}).get("priority_action"), indent=2))
    print("\n-- gc_sec --")
    print(json.dumps(result.get("gc_sec"), indent=2))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Provider Adapter Classes
# ─────────────────────────────────────────────────────────────────────────────
section("6. PROVIDER ADAPTER CLASSES (services/market_data/providers.py)")
set_section("Provider Adapters")

try:
    from services.market_data.providers import CoinGeckoProvider, MutualFundNAVProvider, YahooFinanceProvider
    check("Provider classes importable", True)

    try:
        yp = YahooFinanceProvider("Equity")
        quote = yp.fetch("RELIANCE", exchange="NSE")
        check("YahooFinanceProvider.fetch() - RELIANCE.NS",
              quote.price is not None and quote.price > 0,
              f"Rs {quote.price:,.2f} via {quote.provider}" if quote.price else f"error: {quote.error}")
    except Exception as e:
        check("YahooFinanceProvider.fetch() - RELIANCE.NS", False, str(e))

    try:
        mp = MutualFundNAVProvider()
        with patch("services.market_data.providers.get_settings") as ms:
            ms.return_value = MagicMock(market_data_timeout_seconds=15)
            mq = mp.fetch("119598")
        check("MutualFundNAVProvider.fetch() - scheme 119598",
              mq.price is not None and mq.price > 0,
              f"NAV Rs {mq.price:,.4f}" if mq.price else f"error: {mq.error}")
    except Exception as e:
        check("MutualFundNAVProvider.fetch() - scheme 119598", False, str(e))

    try:
        cp = CoinGeckoProvider()
        with patch("services.market_data.providers.get_settings") as ms:
            ms.return_value = MagicMock(market_data_timeout_seconds=15, coingecko_api_key=None)
            cq = cp.fetch("BTC")
        check("CoinGeckoProvider.fetch() - BTC/INR",
              cq.price is not None and cq.price > 0,
              f"Rs {cq.price:,.0f}" if cq.price else f"error: {cq.error}")
    except Exception as e:
        check("CoinGeckoProvider.fetch() - BTC/INR", False, str(e))

except Exception as e:
    check("Provider classes importable", False, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
section("SUMMARY")
passed = sum(1 for _, _, s in results if s == "PASS")
failed = sum(1 for _, _, s in results if s == "FAIL")
warned = sum(1 for _, _, s in results if s == "WARN")
total  = len(results)

print(f"\n  Total checks : {total}")
print(f"  Passed       : {passed}")
print(f"  Failed       : {failed}")
print(f"  Warnings     : {warned}")

if failed == 0:
    print(f"\n  ALL CHECKS PASSED - Insights tab implementation is working correctly.")
else:
    print(f"\n  {failed} CHECK(S) FAILED - see above for details.")
    print("\nFailed checks:")
    for sec, name, status in results:
        if status == "FAIL":
            print(f"  [{sec}] {name}")

sys.exit(0 if failed == 0 else 1)
