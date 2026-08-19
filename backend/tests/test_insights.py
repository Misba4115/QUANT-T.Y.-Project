from fastapi.testclient import TestClient

from main import app


def test_insights_is_user_scoped_read_only_and_never_recommends(fake_db):
    client = TestClient(app)
    registered = client.post("/api/auth/register", json={"name":"Insight User","email":"insight@example.com","password":"SecurePassword123!","monthly_income":100000,"monthly_expenses":30000})
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    before = {name: len(rows) for name, rows in fake_db.tables.items()}
    response = client.get("/api/insights/readiness", headers=headers)
    after = {name: len(rows) for name, rows in fake_db.tables.items()}
    assert response.status_code == 200
    assert response.json()["algorithm_status"] == "not_implemented"
    assert response.json()["recommendations"] == []
    assert {name: rows for name, rows in before.items() if rows} == {
        name: count for name, count in after.items() if count
    }


def test_no_recommendation_generation_route_exists():
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/insights/generate-recommendations" not in paths
