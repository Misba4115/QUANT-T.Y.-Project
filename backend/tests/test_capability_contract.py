from fastapi.testclient import TestClient

from core.capabilities import STATUS_VOCABULARY, build_capability_registry
from core.config import get_settings
from main import app


def test_registry_covers_phase_2_5_capabilities_and_layers():
    registry = build_capability_registry(get_settings())

    assert set(registry.capabilities) >= {
        "database", "llm", "qdrant", "market_data", "worker", "smtp", "upstox",
        "ingestion_inbox", "parsers", "insights", "grounding_checker",
        "consensus_arbiter", "outcome_evaluator",
    }
    assert registry.status_vocabulary == STATUS_VOCABULARY
    assert [layer.layer for layer in registry.intelligence_layers] == [1, 2, 3]
    assert registry.intelligence_layers[2].capability_id == "outcome_evaluator"
    assert "never changes" in registry.intelligence_layers[2].mutation_policy


def test_capabilities_endpoint_is_machine_readable_and_truthful():
    response = TestClient(app).get("/api/capabilities/")

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "2.5.0"
    assert body["capabilities"]["database"]["status"] == "not_configured"
    assert body["capabilities"]["insights"]["status"] == "partial"
    assert body["capabilities"]["insights"]["reason_code"] == "readiness_only_algorithm_deferred"
    assert body["capabilities"]["qdrant"]["status"] == "partial"
    assert body["capabilities"]["qdrant"]["reason_code"] == "live_probe_required"


def test_readiness_preserves_legacy_status_and_adds_canonical_fields():
    response = TestClient(app).get("/api/readiness")

    assert response.status_code == 200
    body = response.json()
    database = body["dependencies"]["database"]
    assert database["status"] == "unavailable"
    assert database["capability_status"] == "not_configured"
    assert database["reason_code"] == "missing_configuration"
    assert database["retryable"] is False
    assert body["dependencies"]["statement_inbox"] == body["dependencies"]["ingestion_inbox"]
