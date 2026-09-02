import httpx, sys

KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVud2hqcXlqeWV0d3hhbGh5aWNvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjU0OTEzMywiZXhwIjoyMDg4MTI1MTMzfQ"
    ".ykWwu_BbI3miUWf4aXazVQvfpXZzeZ-FlwkAkYhtMPw"
)
BASE = "https://unwhjqyjyetwxalhyico.supabase.co/rest/v1"
HEADERS = {"apikey": KEY, "Authorization": "Bearer " + KEY}

with open("scripts/table_check_out.txt", "w") as f:
    for table in ["price_sync_runs", "market_price_history", "market_price_cache"]:
        r = httpx.get(f"{BASE}/{table}?select=*&limit=1", headers=HEADERS)
        f.write(f"{table}: status={r.status_code} body={r.text[:200]}\n")
    f.flush()
print("Done - see scripts/table_check_out.txt")
