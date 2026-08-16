from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import httpx

from main import app
from services.analytics import indicator_series, synthetic_regimes, walk_forward_forecast
from services.connectors.base import AuthorizationRequired
from services.connectors.upstox import UpstoxConnector
from services.guardian_stream import GuardianStreamService
from services.inbox_ingestion import AttachmentRejected, AttachmentScanner, InboxIngestionService, MemoryBlobStore
from services.notifications import NotificationService, redact_outbound
from services.notification_delivery import NotificationDeliveryService
from services.jobs import JobService
from services.personalization import PersonalizationService
from services.report_export import ReportExportService


def _register(client: TestClient, email: str) -> tuple[dict[str, str], str]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Future User", "email": email, "password": "SecurePassword123!"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, response.json()["access_token"]


def test_sandbox_connector_preview_commit_is_idempotent_and_revocable(fake_db):
    client = TestClient(app)
    headers, _ = _register(client, "connector@example.com")
    created = client.post(
        "/api/connectors/sandbox",
        headers=headers,
        json={"holdings": [{"symbol": "INFY", "name": "Infosys", "quantity": 2, "average_price": 1500}]},
    )
    assert created.status_code == 200, created.text
    account_id = created.json()["connector_account_id"]
    assert "encrypted_credentials" not in created.json()

    preview = client.post(f"/api/connectors/{account_id}/sync/preview", headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["additions"] == 1
    run_id = preview.json()["connector_sync_run_id"]
    committed = client.post(f"/api/connectors/sync/{run_id}/commit", headers=headers)
    assert committed.status_code == 200, committed.text
    assert len(fake_db.tables["equity_holdings"]) == 1
    assert fake_db.tables["equity_holdings"][0]["source_provider"] == "sandbox"

    second = client.post(f"/api/connectors/{account_id}/sync/preview", headers=headers)
    assert second.json()["duplicates"] == 1
    assert client.delete(f"/api/connectors/{account_id}", headers=headers).status_code == 204
    assert fake_db.tables["connector_accounts"][0]["encrypted_credentials"] is None


def test_upstox_contract_normalizes_holdings_and_rejects_expired_auth():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/user/profile"):
            return httpx.Response(200, json={"data": {"user_id": "UP123", "user_name": "Investor"}})
        if request.url.path.endswith("/long-term-holdings"):
            return httpx.Response(200, json={"data": [{"instrument_token": "NSE_EQ|INE009A01021", "trading_symbol": "INFY", "company_name": "Infosys", "quantity": 3, "average_price": 1400, "exchange": "NSE", "isin": "INE009A01021"}]})
        return httpx.Response(401, json={"status": "error"})

    connector = UpstoxConnector("token", httpx.Client(transport=httpx.MockTransport(handler)))
    assert connector.get_profile()["user_id"] == "UP123"
    holding = connector.get_holdings()[0]
    assert holding.instrument_key == "INFY" and holding.quantity == 3
    try:
        connector.get_orders()
        assert False, "expired authorization should not be accepted"
    except AuthorizationRequired:
        pass


def test_one_shot_jobs_do_not_disable_a_users_recurring_schedule(fake_db):
    client = TestClient(app)
    _headers, _ = _register(client, "jobs@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    jobs = JobService(fake_db)
    recurring = jobs.ensure_schedule("price_sync", user_id, 3600)
    one_shot = jobs.enqueue_once("price_sync", user_id, {"reason": "material_change"})
    assert recurring["job_schedule_id"] != one_shot["job_schedule_id"]
    assert one_shot["config"]["base_job_type"] == "price_sync"
    assert len(fake_db.tables["job_schedules"]) == 2


def test_notifications_redact_dedupe_and_respect_user_scope(fake_db):
    client = TestClient(app)
    headers, _ = _register(client, "notify@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    service = NotificationService(fake_db)
    first = service.create(
        user_id=user_id, event_key="risk:1", category="guardian", severity="warning",
        title="Review activity", body="Account 123456789012 belongs to USER@EXAMPLE.COM",
    )
    second = service.create(
        user_id=user_id, event_key="risk:1", category="guardian", severity="warning",
        title="Review activity", body="duplicate",
    )
    assert first["notification_id"] == second["notification_id"]
    payload = service.email_payload(first)
    assert "123456789012" not in payload["body"] and "USER@EXAMPLE.COM" not in payload["body"]
    assert "ABCPD1234Q" not in redact_outbound("PAN ABCPD1234Q")
    assert client.get("/api/notifications", headers=headers).json()[0]["event_key"] == "risk:1"
    response = client.put(
        "/api/notifications/preferences", headers=headers,
        json={"email_enabled": True, "minimum_severity": "warning", "quiet_hours_start": "22:00", "quiet_hours_end": "07:00"},
    )
    assert response.status_code == 200, response.text
    service.update_preferences(user_id, {"quiet_hours_start": None, "quiet_hours_end": None})
    outbound: list[tuple[str, str, str]] = []

    class CapturingEmail:
        def send(self, recipient: str, subject: str, body: str) -> None:
            outbound.append((recipient, subject, body))

    service.create(
        user_id=user_id, event_key="risk:2", category="guardian", severity="critical",
        title="Holding ABC has account 123456789012", body="Raw transaction SHOP USER@EXAMPLE.COM",
    )
    result = NotificationDeliveryService(fake_db, CapturingEmail()).process_pending(user_id)
    assert result["sent"] == 1 and len(outbound) == 1
    assert "ABC" not in outbound[0][1] and "123456789012" not in outbound[0][2]


def test_forwarded_statement_requires_safe_attachment_and_creates_review(fake_db):
    client = TestClient(app)
    _headers, _ = _register(client, "inbox@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    store = MemoryBlobStore()
    service = InboxIngestionService(fake_db, blob_store=store)
    setup = service.create_or_rotate_inbox(user_id, ["inbox@example.com"])
    token = setup["forwarding_address"].split("+")[1].split("@")[0]
    content = b"symbol,equity_name,exchange,quantity,avg_price\nTCS,Tata Consultancy Services,NSE,2,3000\n"
    result = __import__("asyncio").run(
        service.receive(
            address_token=token, external_message_id="message-1", sender="inbox@example.com",
            filename="statement.csv", content_type="text/csv", content=content,
        )
    )
    assert result["status"] == "review_ready"
    assert result["import_batch_id"]
    assert store.values and next(iter(store.values.values())) != content
    duplicate = __import__("asyncio").run(
        service.receive(
            address_token=token, external_message_id="message-1", sender="inbox@example.com",
            filename="statement.csv", content_type="text/csv", content=content,
        )
    )
    assert duplicate["duplicate"] is True
    try:
        AttachmentScanner().scan("malware.csv", b"MZ executable")
        assert False, "executable attachment should be rejected"
    except AttachmentRejected:
        pass


def test_guardian_replay_personalization_and_feedback(fake_db):
    client = TestClient(app)
    _headers, _ = _register(client, "guardian-stream@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    guardian = GuardianStreamService(fake_db)
    event = guardian.ingest(
        user_id=user_id, event_id="evt-1", asset_type="equity", event_type="holding_update",
        occurred_at=datetime.now(timezone.utc), payload={"amount": -10, "portfolio_weight": 0.6},
    )
    assert event["duplicate"] is False
    assert guardian.ingest(
        user_id=user_id, event_id="evt-1", asset_type="equity", event_type="holding_update",
        occurred_at=datetime.now(timezone.utc), payload={"amount": -10},
    )["duplicate"] is True
    processed = guardian.process_pending(user_id)
    assert processed["alerts_created"] == 2
    assert guardian.process_pending(user_id)["alerts_created"] == 0
    alert = guardian.alerts(user_id)[0]
    feedback = guardian.feedback(user_id, alert["guardian_alert_id"], "investigate", "Review source")
    assert feedback["verdict"] == "investigate"

    personalization = PersonalizationService(fake_db)
    inputs = {
        "loss_tolerance": 3, "emergency_months": 9, "time_horizon_years": 12,
        "income_stability": 3, "liability_ratio": 0.2, "concentration_ratio": 0.25,
        "illiquid_ratio": 0.1, "knowledge_level": 2,
    }
    first = personalization.assess(user_id, inputs)
    second = personalization.assess(user_id, inputs)
    assert first["overall_score"] == second["overall_score"]
    prefs = personalization.update_preferences(user_id, {"persona": "analytical"})
    assert prefs["persona"] == "analytical"


def test_indicators_forecast_synthetic_and_signed_exports(fake_db):
    client = TestClient(app)
    _headers, _ = _register(client, "analytics@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    dates = [(datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)).date().isoformat() for index in range(90)]
    prices = [100 + index * 0.4 + (index % 5) * 0.1 for index in range(90)]
    indicators = indicator_series(dates, prices)
    assert indicators["latest"]["rsi_14"] is not None
    assert indicators["maximum_drawdown"] <= 0
    forecast = walk_forward_forecast(prices)
    assert forecast["status"] in {"research_candidate", "experimental_underperforming_baseline"}
    assert synthetic_regimes(42, 100) == synthetic_regimes(42, 100)

    exporter = ReportExportService(fake_db)
    requested = exporter.request(user_id, format="pdf", params={"time_period": "1y", "chart": "portfolio_history"})
    filename, media, content = exporter.render(user_id, requested["report_export_id"], requested["download_token"])
    assert filename.endswith(".pdf") and media == "application/pdf" and content.startswith(b"%PDF")
    png = exporter.request(user_id, format="png", params={"time_period": "1y", "chart": "portfolio_history"})
    _, png_media, png_content = exporter.render(user_id, png["report_export_id"], png["download_token"])
    assert png_media == "image/png" and png_content.startswith(b"\x89PNG")
