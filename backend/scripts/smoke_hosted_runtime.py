"""End-to-end hosted runtime smoke test using disposable synthetic data."""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

from db.supabase_client import get_supabase_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-hosted-smoke", action="store_true")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api")
    parser.add_argument("--mixed-file", type=Path)
    args = parser.parse_args()
    if not args.confirm_hosted_smoke:
        raise SystemExit("Refusing to create hosted smoke data without --confirm-hosted-smoke")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    email = f"quant-smoke-{stamp}-{uuid4().hex[:8]}@example.com"
    user_id: str | None = None
    checks: list[str] = []

    try:
        with httpx.Client(base_url=args.api_url, timeout=30) as client:
            registered = client.post(
                "/auth/register",
                json={
                    "name": "QUANT Hosted Smoke Test",
                    "email": email,
                    "password": "SyntheticSmokePassword123!",
                },
            )
            registered.raise_for_status()
            cookie_header = registered.headers.get("set-cookie", "").lower()
            assert "quant_session=" in cookie_header and "httponly" in cookie_header
            checks.append("registration + HttpOnly cookie")

            profile = client.get("/auth/me")
            profile.raise_for_status()
            user_id = profile.json()["user_id"]
            assert profile.json()["email"] == email
            checks.append("cookie-authenticated profile")

            csv_bytes = (
                "Security Code,Holding Units,Acquisition Cost,Personal Note\n"
                "SMOKETEST,1,100,ignored reference field\n"
            ).encode()
            diagnostic = client.post(
                "/imports/preview",
                files={"file": ("quant-smoke.csv", csv_bytes, "text/csv")},
            )
            if diagnostic.status_code == 200:
                preview = diagnostic
                assert preview.json()["column_mapping"]["method"] == "llm_headers"
                checks.append("unfamiliar headers mapped automatically by LLM")
            else:
                assert diagnostic.status_code == 422
                assert diagnostic.json()["detail"]["code"] == "mapping_required"
                checks.append("unfamiliar table requested guided mapping")
                preview = client.post(
                    "/imports/preview",
                    data={
                        "target_type": "equity_holdings",
                        "column_mapping": json.dumps(
                            {
                                "Security Code": "symbol",
                                "Holding Units": "quantity",
                                "Acquisition Cost": "avg_price",
                            }
                        ),
                    },
                    files={"file": ("quant-smoke.csv", csv_bytes, "text/csv")},
                )
            preview.raise_for_status()
            batch = preview.json()
            assert batch["valid_count"] == 1 and batch["target_type"] == "equity_holdings"
            assert batch["column_mapping"]["source_to_canonical"]["Holding Units"] == "quantity"
            assert batch["column_mapping"]["ignored_columns"] == ["Personal Note"]
            checks.append("guided mapping preview + ignored-column evidence")

            cleaned = client.get(f"/imports/{batch['import_batch_id']}/normalized.csv")
            cleaned.raise_for_status()
            cleaned_headers = set(
                csv.DictReader(io.StringIO(cleaned.content.decode("utf-8-sig"))).fieldnames or []
            )
            assert {"symbol", "equity_name", "quantity", "avg_price"}.issubset(cleaned_headers)
            assert "Personal Note" not in cleaned.text
            checks.append("user-scoped cleaned CSV download")

            committed = client.post(
                f"/imports/{batch['import_batch_id']}/commit",
                json={"column_mapping": {}},
            )
            committed.raise_for_status()
            assert committed.json()["committed_count"] == 1
            checks.append("CSV commit persisted")

            if args.mixed_file:
                mixed_bytes = args.mixed_file.read_bytes()
                mixed_preview = client.post(
                    "/imports/preview",
                    files={"file": (args.mixed_file.name, mixed_bytes, "text/csv")},
                )
                mixed_preview.raise_for_status()
                mixed_batch = mixed_preview.json()
                assert mixed_batch["target_type"] == "mixed_asset_transactions"
                assert mixed_batch["valid_count"] == 76
                mixed_commit = client.post(
                    f"/imports/{mixed_batch['import_batch_id']}/commit",
                    json={"column_mapping": {}},
                )
                mixed_commit.raise_for_status()
                assert mixed_commit.json()["committed_count"] == 76
                checks.append("76-row mixed investment history split and committed")

            logged_out = client.post("/auth/logout")
            assert logged_out.status_code == 204
            assert client.get("/auth/me").status_code == 401
            checks.append("logout cleared session")
    finally:
        database = get_supabase_client()
        query = database.table("users").select("user_id,email").eq("email", email).limit(2).execute()
        rows = query.data or []
        if rows:
            if len(rows) != 1 or (user_id and str(rows[0]["user_id"]) != str(user_id)):
                raise RuntimeError("Smoke cleanup identity check failed; no rows were deleted")
            database.table("users").delete().eq("user_id", rows[0]["user_id"]).eq("email", email).execute()
            remaining = database.table("users").select("user_id").eq("email", email).limit(1).execute()
            if remaining.data:
                raise RuntimeError("Smoke cleanup failed")
        checks.append("synthetic account and cascaded data removed")

    print("Hosted smoke test passed:")
    for check in checks:
        print(f"- {check}")


if __name__ == "__main__":
    main()
