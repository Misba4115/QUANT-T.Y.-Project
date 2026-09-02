"""
Demo Snapshot Seeder
=====================
Inserts 30 days of realistic portfolio_snapshots for ONE user so that
the Insights tab Market Outlook cards show real directional EWMA charts
instead of the flat -20% to +20% fallback.

Usage:
    cd backend
    python scripts/seed_demo_snapshots.py <user_id>

To find your user_id:  open Supabase → Table Editor → users → copy the user_id UUID.

What it does:
  - Generates 30 daily portfolio snapshot rows (going back from today)
  - Each row has per-asset-class values with realistic drift:
      Equity:      +8%  annualised trend (bullish for demo)
      Mutual Fund: +6%  annualised trend
      ETF:         +5%  annualised trend
  - Upserts by (user_id, snapshot_date) so safe to run multiple times
"""
from __future__ import annotations

import math
import random
import sys
from datetime import date, timedelta

from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://unwhjqyjyetwxalhyico.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVud2hqcXlqeWV0d3hhbGh5aWNvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjU0OTEzMywiZXhwIjoyMDg4MTI1MTMzfQ"
    ".ykWwu_BbI3miUWf4aXazVQvfpXZzeZ-FlwkAkYhtMPw"
)

# ── Base portfolio values (current, from your uploaded CSVs) ──────────────────
# Equity:  7 stocks  → 166,450
# MF:      7 funds   → 79,855
# ETF:     7 ETFs    → 35,098
BASE_VALUES = {
    "Equity":      166_450.0,
    "Mutual Fund":  79_855.0,
    "ETF":          35_098.0,
}

# Annual drift per asset class (as decimal, e.g. 0.08 = 8% p.a.)
ANNUAL_DRIFT = {
    "Equity":      0.08,
    "Mutual Fund": 0.06,
    "ETF":         0.05,
}

# Annual volatility
ANNUAL_VOL = {
    "Equity":      0.18,
    "Mutual Fund": 0.10,
    "ETF":         0.12,
}

DAYS = 30
SEED = 42   # fixed seed → reproducible chart shape


def simulate_prices(base: float, drift: float, vol: float, days: int, seed: int) -> list[float]:
    """Geometric Brownian Motion backwards from today's base value."""
    rng = random.Random(seed)
    daily_drift = drift / 252
    daily_vol = vol / math.sqrt(252)

    prices = [base]
    for _ in range(days - 1):
        shock = rng.gauss(0, 1)
        ret = daily_drift + daily_vol * shock
        prices.append(prices[-1] / (1 + ret))  # reverse: past = current / (1+r)
    prices.reverse()
    return prices


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_demo_snapshots.py <user_id>")
        print("\nTo find your user_id:")
        print("  Supabase Dashboard → Table Editor → users → copy the UUID in user_id column")
        sys.exit(1)

    user_id = sys.argv[1].strip()
    print(f"\n  Seeding 30-day portfolio snapshots for user: {user_id}")
    print(f"    Supabase: {SUPABASE_URL}\n")

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verify user exists
    user_check = db.table("users").select("user_id,name").eq("user_id", user_id).limit(1).execute()
    if not user_check.data:
        print(f"ERROR: No user found with user_id = {user_id}")
        print("    Check Supabase Dashboard -> Table Editor -> users for the correct UUID.")
        sys.exit(1)
    user_name = user_check.data[0].get("name", "Unknown")
    print(f"Found user: {user_name}")

    # Generate price series for each asset class
    price_series: dict[str, list[float]] = {}
    for asset_class, base in BASE_VALUES.items():
        price_series[asset_class] = simulate_prices(
            base,
            ANNUAL_DRIFT[asset_class],
            ANNUAL_VOL[asset_class],
            DAYS,
            seed=SEED + hash(asset_class) % 1000,
        )

    today = date.today()
    inserted = 0
    updated = 0

    for i in range(DAYS):
        snap_date = (today - timedelta(days=DAYS - 1 - i)).isoformat()
        net_worth = sum(series[i] for series in price_series.values())
        allocation = {
            ac: round(price_series[ac][i] / net_worth * 100, 2)
            for ac in BASE_VALUES
        }

        payload = {
            "user_id":            user_id,
            "snapshot_date":      snap_date,
            "net_worth":          round(net_worth, 2),
            "total_value":        round(net_worth, 2),
            "allocation":         allocation,
            "valuation_coverage": 1.0,
            "source_status":      "seeded_for_demo",
        }

        existing = (
            db.table("portfolio_snapshots")
            .select("snapshot_id")
            .eq("user_id", user_id)
            .eq("snapshot_date", snap_date)
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            db.table("portfolio_snapshots").update(payload).eq("snapshot_id", existing[0]["snapshot_id"]).execute()
            updated += 1
        else:
            db.table("portfolio_snapshots").insert(payload).execute()
            inserted += 1

        if i % 5 == 0:
            print(f"  {snap_date}  net_worth={net_worth:>12,.0f}")

    print(f"\nDone!  inserted={inserted}  updated={updated}")
    print("\nNext steps:")
    print("  1. Open the Insights & Trading tab in your browser")
    print("  2. Click 'Refresh now' to force-regenerate insights")
    print("  3. Market Outlook cards will now show directional charts")
    print()
    print("Expected chart directions after seeding:")
    for ac, drift in ANNUAL_DRIFT.items():
        arrow = "up" if drift > 0 else "down"
        print(f"  {ac:<15}  {arrow}  ({drift*100:+.0f}% annual drift)")


if __name__ == "__main__":
    main()
