from fastapi.testclient import TestClient

from main import app


def test_market_capability_is_truthful_about_single_provider_limitations():
    body = TestClient(app).get("/api/market-data/capabilities").json()
    assert body["redundancy_status"] == "not_configured"
    assert all("single_provider" in item["limitations"] for item in body["providers"])
    assert all(item["status"] == "experimental" for item in body["providers"])


def test_parser_capability_does_not_advertise_ocr_or_unknown_layouts():
    body = TestClient(app).get("/api/imports/capabilities").json()
    assert body["ocr"]["status"] == "not_configured"
    assert body["ocr"]["low_confidence_auto_commit"] is False
    assert body["unknown_layout_policy"].startswith("reject")
