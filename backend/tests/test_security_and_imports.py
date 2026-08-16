from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from main import app
from services.file_parser import analyze_financial_file, normalize_row, parse_financial_file, tabular_column_profiles
from services.import_mapping_service import validate_mapping_suggestion


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "name": email.split("@")[0],
            "email": email,
            "password": "SecurePassword123!",
            "age": 30,
            "monthly_income": 100000,
            "monthly_expenses": 40000,
            "primary_goal": "wealth",
            "risk_profile": "moderate",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_registration_defers_optional_financial_profile_to_onboarding(fake_db):
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"name": "New User", "email": "new@example.com", "password": "SecurePassword123!"},
    )
    assert response.status_code == 201, response.text
    created = fake_db.tables["users"][-1]
    assert created["age"] is None
    assert created["primary_goal"] is None


def test_http_only_cookie_session_and_logout(fake_db):
    client = TestClient(app)
    registered = client.post(
        "/api/auth/register",
        json={"name": "Cookie User", "email": "cookie@example.com", "password": "SecurePassword123!"},
    )
    assert registered.status_code == 201, registered.text
    set_cookie = registered.headers["set-cookie"].lower()
    assert "quant_session=" in set_cookie
    assert "httponly" in set_cookie

    # No Authorization header: the HttpOnly cookie authenticates the request.
    profile = client.get("/api/auth/me")
    assert profile.status_code == 200, profile.text
    assert profile.json()["email"] == "cookie@example.com"

    logged_out = client.post("/api/auth/logout")
    assert logged_out.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_cross_user_account_and_mass_assignment_are_blocked(fake_db):
    client = TestClient(app)
    alice = _register(client, "alice@example.com")
    bob = _register(client, "bob@example.com")
    created = client.post(
        "/api/banking-accounts/",
        headers=alice,
        json={
            "account_type": "savings",
            "account_name": "Alice savings",
            "institution": "Example Bank",
            "current_balance": 50000,
        },
    )
    assert created.status_code == 201, created.text
    account_id = created.json()["account_id"]

    assert client.put(
        f"/api/banking-accounts/{account_id}", headers=bob, json={"current_balance": 1}
    ).status_code == 404
    assert client.post(
        "/api/transactions/bank",
        headers=bob,
        json={
            "account_id": account_id,
            "tx_date": "2026-08-01",
            "description": "Cross-user attempt",
            "amount": 100,
            "tx_type": "debit",
        },
    ).status_code == 422

    mass_assignment = client.put(
        "/api/user/profile",
        headers=alice,
        json={"email": "attacker@example.com", "password_hash": "owned"},
    )
    assert mass_assignment.status_code == 422
    alice_row = next(row for row in fake_db.tables["users"] if row["email"] == "alice@example.com")
    assert alice_row["email"] == "alice@example.com"
    assert alice_row["password_hash"] != "owned"


def test_import_preview_commit_is_idempotent_and_user_scoped(fake_db):
    client = TestClient(app)
    alice = _register(client, "importer@example.com")
    bob = _register(client, "other@example.com")
    content = (
        "symbol,equity_name,exchange,quantity,avg_price,current_price,broker\n"
        "INFY,Infosys Limited,NSE,4,1500,1800,Zerodha\n"
        "HDFCBANK,HDFC Bank Limited,NSE,2,1600,1700,Zerodha\n"
    ).encode()

    preview = client.post(
        "/api/imports/preview",
        headers=alice,
        files={"file": ("holdings.csv", content, "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["target_type"] == "equity_holdings"
    assert body["valid_count"] == 2
    assert fake_db.tables.get("equity_holdings", []) == []
    batch_id = body["import_batch_id"]

    assert client.get(f"/api/imports/{batch_id}", headers=bob).status_code == 404
    assert client.post(f"/api/imports/{batch_id}/commit", headers=bob, json={}).status_code == 404

    committed = client.post(f"/api/imports/{batch_id}/commit", headers=alice, json={})
    assert committed.status_code == 200, committed.text
    assert committed.json()["committed_count"] == 2
    assert len(fake_db.tables["equity_holdings"]) == 2

    repeated_commit = client.post(f"/api/imports/{batch_id}/commit", headers=alice, json={})
    assert repeated_commit.status_code == 200
    assert repeated_commit.json()["duplicate"] is True
    assert len(fake_db.tables["equity_holdings"]) == 2

    repeated_preview = client.post(
        "/api/imports/preview",
        headers=alice,
        files={"file": ("holdings.csv", content, "text/csv")},
    )
    assert repeated_preview.status_code == 200
    assert repeated_preview.json()["import_batch_id"] == batch_id
    assert repeated_preview.json()["duplicate"] is True


def test_import_library_persists_cleaned_user_owned_previews(fake_db):
    client = TestClient(app)
    alice = _register(client, "library@example.com")
    bob = _register(client, "library-other@example.com")
    content = (
        "symbol,equity_name,exchange,quantity,avg_price,current_price,broker\n"
        "INFY,Infosys Limited,NSE,4,1500,1800,Zerodha\n"
    ).encode()
    preview = client.post(
        "/api/imports/preview",
        headers=alice,
        files={"file": ("holdings.csv", content, "text/csv")},
    ).json()

    library = client.get("/api/imports", headers=alice)
    assert library.status_code == 200, library.text
    assert len(library.json()) == 1
    assert library.json()[0]["import_batch_id"] == preview["import_batch_id"]
    assert library.json()[0]["preview_rows"] == []
    assert library.json()[0]["created_at"]
    assert client.get("/api/imports", headers=bob).json() == []

    reopened = client.get(f"/api/imports/{preview['import_batch_id']}", headers=alice)
    assert reopened.status_code == 200
    assert len(reopened.json()["preview_rows"]) == 1

    downloaded = client.get(
        f"/api/imports/{preview['import_batch_id']}/normalized.csv", headers=alice
    )
    assert downloaded.status_code == 200
    assert "INFY" in downloaded.text


def test_import_commit_succeeds_when_optional_guardian_schema_is_unavailable(fake_db, monkeypatch):
    from services.guardian_stream import GuardianStreamService
    from services.jobs import JobService

    client = TestClient(app)
    headers = _register(client, "guardian-independent@example.com")
    content = (
        "symbol,equity_name,exchange,quantity,avg_price,current_price,broker\n"
        "INFY,Infosys Limited,NSE,4,1500,1800,Zerodha\n"
    ).encode()
    preview = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("holdings.csv", content, "text/csv")},
    )
    assert preview.status_code == 200, preview.text

    def missing_guardian_table(*args, **kwargs):
        raise RuntimeError(
            "{'message': \"Could not find the table 'public.guardian_events' in the schema cache\", "
            "'code': 'PGRST205'}"
        )

    monkeypatch.setattr(GuardianStreamService, "ingest", missing_guardian_table)
    monkeypatch.setattr(JobService, "enqueue_once", missing_guardian_table)
    committed = client.post(
        f"/api/imports/{preview.json()['import_batch_id']}/commit", headers=headers, json={}
    )

    assert committed.status_code == 200, committed.text
    assert committed.json()["status"] == "completed"
    assert committed.json()["committed_count"] == 1
    assert committed.json()["row_errors"] == []
    assert len(fake_db.tables["equity_holdings"]) == 1


def test_partial_import_retry_reconciles_rows_and_clears_stale_commit_errors(fake_db):
    client = TestClient(app)
    headers = _register(client, "partial-retry@example.com")
    content = (
        "symbol,equity_name,exchange,quantity,avg_price,current_price,broker\n"
        "INFY,Infosys Limited,NSE,4,1500,1800,Zerodha\n"
    ).encode()
    preview = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("holdings.csv", content, "text/csv")},
    ).json()
    batch_id = preview["import_batch_id"]
    assert client.post(f"/api/imports/{batch_id}/commit", headers=headers, json={}).status_code == 200

    fake_db.table("import_batches").update(
        {"status": "partial", "committed_count": 0, "error_count": 1}
    ).eq("import_batch_id", batch_id).execute()
    fake_db.table("import_row_errors").insert(
        {
            "import_batch_id": batch_id,
            "row_number": 2,
            "code": "commit_failed",
            "message": "optional downstream table unavailable",
            "raw_row": {},
        }
    ).execute()

    retried = client.post(f"/api/imports/{batch_id}/commit", headers=headers, json={})
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "completed"
    assert retried.json()["committed_count"] == 1
    assert retried.json()["error_count"] == 0
    assert retried.json()["row_errors"] == []
    assert len(fake_db.tables["equity_holdings"]) == 1


def test_bad_dates_are_reported_and_never_default_to_today(fake_db):
    client = TestClient(app)
    headers = _register(client, "dates@example.com")
    content = (
        "tx_date,description,amount,tx_type\n"
        "not-a-date,Unknown date,100,debit\n"
    ).encode()
    response = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("transactions.csv", content, "text/csv")},
    )
    assert response.status_code == 422
    assert fake_db.tables.get("bank_transactions", []) == []


def test_transaction_import_resolves_owned_account_type(fake_db):
    client = TestClient(app)
    headers = _register(client, "transactions@example.com")
    account = client.post(
        "/api/banking-accounts/",
        headers=headers,
        json={
            "account_type": "savings",
            "account_name": "Primary",
            "institution": "Example Bank",
            "current_balance": 1000,
        },
    ).json()
    content = (
        "account_id,tx_date,description,amount,tx_type,category\n"
        "savings,2026-08-01,Salary,100000,credit,Salary\n"
        "savings,2026-08-02,Groceries,-2500,debit,Food\n"
    ).encode()
    preview = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("transactions.csv", content, "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    committed = client.post(
        f"/api/imports/{preview.json()['import_batch_id']}/commit", headers=headers, json={}
    )
    assert committed.status_code == 200, committed.text
    assert committed.json()["committed_count"] == 2
    assert {row["account_id"] for row in fake_db.tables["bank_transactions"]} == {account["account_id"]}
    assert {row["amount"] for row in fake_db.tables["bank_transactions"]} == {100000.0, 2500.0}


def test_every_checked_in_sample_csv_is_detected_and_normalized():
    sample_dir = Path(__file__).resolve().parents[2] / "sample_data"
    expected = {
        "crypto_holdings.csv": "crypto_holdings",
        "equities.csv": "equity_holdings",
        "etfs.csv": "etf_holdings",
        "mutual_funds.csv": "mutual_fund_holdings",
        "transactions.csv": "bank_transactions",
    }
    for filename, target in expected.items():
        detected, rows = parse_financial_file(filename, (sample_dir / filename).read_bytes())
        assert detected == target
        assert rows, filename
        assert all(normalize_row(detected, row) for row in rows)

    for manual_only in ("banking_accounts.csv", "goals.csv"):
        with pytest.raises(ValueError, match="entered directly in Input Data"):
            parse_financial_file(manual_only, (sample_dir / manual_only).read_bytes())


def test_arbitrary_csv_gets_actionable_template_guidance():
    insurance_sample = b"age,bought_insurance\n22,0\n47,1\n"
    try:
        parse_financial_file("insurance_data.csv", insurance_sample)
    except ValueError as exc:
        message = str(exc)
        assert "file structure is not recognized" in message.lower()
        assert "input data" in message.lower()
    else:
        raise AssertionError("An arbitrary ML dataset must not be treated as a financial import")


def test_alias_mapping_ignored_columns_and_normalized_download_are_user_scoped(fake_db):
    client = TestClient(app)
    alice = _register(client, "mapping-alice@example.com")
    bob = _register(client, "mapping-bob@example.com")
    content = (
        "Stock Symbol,Company Name,Qty,Average Buy Price,Market Price,Broker Notes\n"
        "INFY,=UNSAFE_FORMULA,4,1500,1800,reference only\n"
    ).encode()

    preview = client.post(
        "/api/imports/preview",
        headers=alice,
        files={"file": ("broker-export.csv", content, "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["target_type"] == "equity_holdings"
    mapping = body["column_mapping"]
    assert mapping["source_to_canonical"]["Stock Symbol"] == "symbol"
    assert mapping["source_to_canonical"]["Average Buy Price"] == "avg_price"
    assert mapping["ignored_columns"] == ["Broker Notes"]

    batch_id = body["import_batch_id"]
    denied = client.get(f"/api/imports/{batch_id}/normalized.csv", headers=bob)
    assert denied.status_code == 404

    downloaded = client.get(f"/api/imports/{batch_id}/normalized.csv", headers=alice)
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("text/csv")
    assert "broker-export-normalized.csv" in downloaded.headers["content-disposition"]
    normalized_text = downloaded.content.decode("utf-8-sig")
    assert "symbol,equity_name,exchange,quantity,avg_price,current_price" in normalized_text
    assert "Broker Notes" not in normalized_text
    assert "'=UNSAFE_FORMULA" in normalized_text


def test_unrecognized_financial_table_can_be_mapped_without_editing_the_file(fake_db):
    client = TestClient(app)
    headers = _register(client, "guided-mapping@example.com")
    raw_content = b"Security Code,Holding Units,Acquisition Cost,Personal Note\nTCS,3,3500,keep privately\n"

    first_attempt = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("unfamiliar-broker.csv", raw_content, "text/csv")},
    )
    assert first_attempt.status_code == 422
    diagnostic = first_attempt.json()["detail"]
    assert diagnostic["code"] == "mapping_required"
    assert diagnostic["source_columns"] == [
        "Security Code", "Holding Units", "Acquisition Cost", "Personal Note"
    ]

    mapped_attempt = client.post(
        "/api/imports/preview",
        headers=headers,
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
        files={"file": ("unfamiliar-broker.csv", raw_content, "text/csv")},
    )
    assert mapped_attempt.status_code == 200, mapped_attempt.text
    body = mapped_attempt.json()
    assert body["target_type"] == "equity_holdings"
    assert body["preview_rows"][0]["symbol"] == "TCS"
    assert body["preview_rows"][0]["equity_name"] == "TCS"
    assert body["column_mapping"]["ignored_columns"] == ["Personal Note"]


def test_llm_header_mapping_is_strictly_schema_validated():
    columns = ["Security Code", "Holding Units", "Acquisition Cost", "Notes"]
    accepted = validate_mapping_suggestion(
        {
            "target_type": "equity_holdings",
            "column_mapping": {
                "Security Code": "symbol",
                "Holding Units": "quantity",
                "Acquisition Cost": "avg_price",
                "Made Up": "broker",
            },
            "confidence": 0.93,
        },
        columns,
    )
    assert accepted == {
        "target_type": "equity_holdings",
        "column_mapping": {
            "Security Code": "symbol",
            "Holding Units": "quantity",
            "Acquisition Cost": "avg_price",
        },
        "confidence": 0.93,
    }
    assert validate_mapping_suggestion(
        {
            "target_type": "banking_accounts",
            "column_mapping": {"Security Code": "account_name"},
            "confidence": 0.99,
        },
        columns,
    ) is None
    assert validate_mapping_suggestion(
        {
            "target_type": "equity_holdings",
            "column_mapping": {"Security Code": "symbol"},
            "confidence": 0.99,
        },
        columns,
    ) is None


def test_llm_header_mapping_can_create_a_valid_preview(fake_db, monkeypatch):
    client = TestClient(app)
    headers = _register(client, "ai-mapping@example.com")
    content = b"Security Code,Holding Units,Acquisition Cost,Private Note\nTCS,3,3500,ignore\n"
    monkeypatch.setattr(
        "services.import_service.suggest_import_mapping",
        lambda _columns, _filename=None, _content=None, _file_mode=None: {
            "target_type": "equity_holdings",
            "column_mapping": {
                "Security Code": "symbol",
                "Holding Units": "quantity",
                "Acquisition Cost": "avg_price",
            },
            "confidence": 0.95,
        },
    )
    response = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("ai-broker.csv", content, "text/csv")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_type"] == "equity_holdings"
    assert body["column_mapping"]["method"] == "llm_headers"
    assert body["preview_rows"][0]["symbol"] == "TCS"


def test_mixed_investment_history_splits_rows_into_asset_transaction_tables(fake_db):
    client = TestClient(app)
    headers = _register(client, "mixed-transactions@example.com")
    content = (
        "TransactionID,Date,AssetType,Symbol,AssetName,TransactionType,Quantity,Price,Amount,Platform\n"
        "1,2023-01-03,Stock,RELIANCE,Reliance Industries,BUY,4,2450,9800,Zerodha\n"
        "2,2023-01-15,ETF,NIFTYBEES,Nippon India ETF Nifty 50,SELL,2,200,400,Groww\n"
        "3,2023-02-01,MutualFund,AXISBLUECHIP,Axis Bluechip Fund,SIP,50,40,2000,Groww\n"
    ).encode()

    preview = client.post(
        "/api/imports/preview",
        headers=headers,
        files={"file": ("investment_transactions.csv", content, "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["target_type"] == "mixed_asset_transactions"
    assert body["valid_count"] == 3
    assert {row["asset_type"] for row in body["preview_rows"]} == {"Equity", "ETF", "Mutual Fund"}
    assert {row["tx_type"] for row in body["preview_rows"]} == {"buy", "sell"}

    committed = client.post(
        f"/api/imports/{body['import_batch_id']}/commit",
        headers=headers,
        json={},
    )
    assert committed.status_code == 200, committed.text
    assert committed.json()["committed_count"] == 3
    assert len(fake_db.tables["equity_transactions"]) == 1
    assert len(fake_db.tables["etf_transactions"]) == 1
    assert len(fake_db.tables["mf_transactions"]) == 1
    assert fake_db.tables["mf_transactions"][0]["tx_type"] == "buy"


def test_privacy_safe_profiles_and_unfamiliar_equity_transaction_mapping():
    content = (
        "Execution Day,Security Identifier,Instrument Label,Order Direction,Executed Units,Trade Rate,Venue\n"
        "12/08/2026,ABC123,Example Industries,Purchase,5,120.50,NSE\n"
        "13/08/2026,XYZ789,Example Systems,Sale,2,88.10,BSE\n"
    ).encode()
    profiles = tabular_column_profiles("unknown-broker.csv", content)
    direction = next(item for item in profiles if item["source_column"] == "Order Direction")
    assert direction["category_values"] == ["Purchase", "Sale"]
    identifier = next(item for item in profiles if item["source_column"] == "Security Identifier")
    assert "category_values" not in identifier
    assert "ABC123" not in str(identifier)

    parsed = analyze_financial_file(
        "unknown-broker.csv",
        content,
        "equity_transactions",
        {
            "Execution Day": "tx_date",
            "Security Identifier": "symbol",
            "Order Direction": "tx_type",
            "Executed Units": "quantity",
            "Trade Rate": "price",
        },
    )
    normalized = [normalize_row(parsed.target, row) for row in parsed.rows]
    assert [row["tx_date"] for row in normalized] == ["2026-08-12", "2026-08-13"]
    assert [row["tx_type"] for row in normalized] == ["buy", "sell"]
    assert all(row["_target_table"] == "equity_transactions" for row in normalized)


def test_one_question_file_mode_clarification_retries_mapping(fake_db, monkeypatch):
    client = TestClient(app)
    headers = _register(client, "clarified-import@example.com")
    content = (
        "Execution Day,Security Identifier,Order Direction,Executed Units,Trade Rate\n"
        "12/08/2026,ABC123,Purchase,5,120.50\n"
    ).encode()
    observed: list[str | None] = []

    def suggestion(_columns, _filename=None, _content=None, file_mode=None):
        observed.append(file_mode)
        return {
            "target_type": "equity_transactions",
            "column_mapping": {
                "Execution Day": "tx_date",
                "Security Identifier": "symbol",
                "Order Direction": "tx_type",
                "Executed Units": "quantity",
                "Trade Rate": "price",
            },
            "confidence": 0.94,
        }

    monkeypatch.setattr("services.import_service.suggest_import_mapping", suggestion)
    response = client.post(
        "/api/imports/preview",
        headers=headers,
        data={"file_mode": "investment_history"},
        files={"file": ("unknown-provider.csv", content, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert observed == ["investment_history"]
    assert response.json()["target_type"] == "equity_transactions"


def test_whole_row_quoted_csv_is_recovered_before_classification():
    content = (
        '"Transaction_ID,Date,Account_Type,Asset_Type,Ticker,Security_Name,Transaction_Type,Units,Price_Per_Unit,Fees_Commission"\n'
        '"T1,2026-05-18,Brokerage,ETF,VOO,Vanguard ETF,Buy,10,482.5,0"\n'
        '"T2,2026-05-20,IRA,Mutual Fund,FXAIX,Fidelity Index,SIP / Auto-Invest,5.4,184.77,0"\n'
        '"T3,2026-05-25,Brokerage,ETF,VOO,Vanguard ETF,Dividend Reinvestment,1,485,0"\n'
    ).encode("utf-8-sig")
    parsed = analyze_financial_file("quoted-export.csv", content)
    normalized = [normalize_row(parsed.target, row) for row in parsed.rows]
    assert parsed.target == "mixed_asset_transactions"
    assert len(parsed.source_to_canonical) == 10
    assert len(normalized) == 3
    assert [row["tx_type"] for row in normalized] == ["buy", "buy", "buy"]
    assert {row["_target_table"] for row in normalized} == {"etf_transactions", "mf_transactions"}


def test_semicolon_delimited_bank_export_is_parsed():
    content = (
        "Date;Narration;Withdrawal Amount;Deposit Amount\n"
        "16/08/2026;Card purchase;450;\n"
        "17/08/2026;Transfer received;;5000\n"
    ).encode()
    target, rows = parse_financial_file("regional-bank.csv", content)
    assert target == "bank_transactions"
    normalized = [normalize_row(target, row) for row in rows]
    assert [row["tx_type"] for row in normalized] == ["debit", "credit"]
