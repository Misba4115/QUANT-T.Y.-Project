from fastapi.testclient import TestClient

from main import app


def test_health_is_credential_free():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_readiness_distinguishes_dependencies():
    response = TestClient(app).get("/api/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["database"]["status"] == "unavailable"
    assert body["dependencies"]["database"]["capability_status"] == "not_configured"
    assert body["contract_version"] == "2.5.0"
    assert "llm" in body["dependencies"]
    assert "qdrant" in body["dependencies"]


def test_openapi_uses_api_prefix():
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/auth/register" in paths
    assert "/api/dashboard/generate" in paths
    assert "/api/chat" in paths or "/api/chat/" in paths
    assert not any(path.startswith("/auth/") for path in paths)


def test_validation_error_has_stable_envelope(fake_db):
    response = TestClient(app).post("/api/auth/register", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["request_id"]
    assert body["field_errors"]
