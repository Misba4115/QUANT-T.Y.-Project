import httpx, sys

KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVud2hqcXlqeWV0d3hhbGh5aWNvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjU0OTEzMywiZXhwIjoyMDg4MTI1MTMzfQ"
    ".ykWwu_BbI3miUWf4aXazVQvfpXZzeZ-FlwkAkYhtMPw"
)
BASE = "https://unwhjqyjyetwxalhyico.supabase.co/rest/v1"
HEADERS = {"apikey": KEY, "Authorization": "Bearer " + KEY}

with httpx.Client(timeout=20) as client:
    # List ALL users (limit 20)
    r = client.get(f"{BASE}/users?select=user_id,name,email&limit=20", headers=HEADERS)
    print(f"ALL USERS: status={r.status_code}")
    print(r.text[:800])
    print()
    # Check logged-in user's holdings
    target = "8308e4c1-6a0b-4a4b-b7ea-83c840388f37"
    for table in ["equity_holdings", "etf_holdings", "mutual_fund_holdings", "portfolio_snapshots"]:
        r2 = client.get(f"{BASE}/{table}?select=user_id&user_id=eq.{target}&limit=5", headers=HEADERS)
        print(f"{table} for {target}: {r2.text[:200]}")
    sys.stdout.flush()
