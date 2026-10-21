from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from agents.chat_orchestrator import ChatOrchestrator
from agents.response_grounding import validate_material_numbers
from agents.guardian import run_guardian
from agents.tax import run_tax_agent
from main import app
from routers.chat import get_chat_orchestrator


class FakePublicRAG:
    def search(self, query, limit=5):
        return [
            {
                "citation_id": "public:tax-1", "title": "Official tax guidance",
                "source_type": "public_knowledge", "source_url": "https://example.gov/tax",
                "authority": "Government", "effective_date": "2024-07-23",
                "retrieved_date": "2026-08-12", "excerpt": "Evidence is required.",
                "locator": "section 1", "similarity": 0.85,
            }
        ]


def _llm(messages):
    return "Computed from structured data and the rule [public:tax-1]. Bad [public:invented]."


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Agent User", "email": email, "password": "SecurePassword123!", "age": 31,
            "monthly_income": 100000, "monthly_expenses": 30000, "primary_goal": "wealth", "risk_profile": "moderate",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_langgraph_runs_distinct_nodes_and_validates_citations(fake_db):
    client = TestClient(app)
    _register(client, "graph@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    orchestrator = ChatOrchestrator(fake_db, llm=_llm, public_rag=FakePublicRAG())
    result = orchestrator.run(
        user_id, "Review my portfolio, tax and spending cashflow", "conversation-1"
    )
    assert result["intent"] == "multi_agent"
    assert result["selected_agents"] == ["portfolio", "tax", "cashflow"]
    assert result["completed_nodes"] == [
        "manager", "portfolio", "tax", "cashflow", "retrieve", "generate"
    ]
    assert result["routing"]["primary_intent"] == "cross_domain_analysis"
    assert "[public:tax-1]" in result["reply"]
    assert "public:invented" not in result["reply"]
    assert any("unverified citation" in warning for warning in result["warnings"])
    assert {item["citation_id"] for item in result["citations"]} == {"public:tax-1"}


def test_material_number_validator_keeps_supported_and_removes_invented_figures():
    response = "Your grounded surplus is INR 70,000. A guaranteed return of 18% is expected. You should review the assumptions."
    safe, unsupported = validate_material_numbers(response, {"surplus": 70000, "observed_return": 7.5})
    assert "70,000" in safe
    assert "18%" not in safe
    assert "review the assumptions" in safe
    assert unsupported == ["18%"]


def test_material_number_validator_fails_closed_when_every_figure_is_unverified():
    safe, unsupported = validate_material_numbers("Your portfolio is worth ₹9,99,999.", {"net_worth": None})
    assert "9,99,999" not in safe
    assert unsupported == ["₹9,99,999"]


def test_chat_owns_conversation_and_persists_each_message_once(fake_db):
    client = TestClient(app)
    alice = _register(client, "chat-alice@example.com")
    bob = _register(client, "chat-bob@example.com")
    orchestrator = ChatOrchestrator(
        fake_db, llm=lambda messages: "Grounded reply",
        public_rag=FakePublicRAG(),
    )
    app.dependency_overrides[get_chat_orchestrator] = lambda: orchestrator
    try:
        first = client.post("/api/chat/", headers=alice, json={"message": "Review my portfolio"})
        assert first.status_code == 200, first.text
        conversation_id = first.json()["conversation_id"]
        messages = [row for row in fake_db.tables["chat_messages"] if row["conversation_id"] == conversation_id]
        assert [row["role"] for row in messages] == ["user", "assistant"]

        attack = client.post(
            "/api/chat/", headers=bob,
            json={"message": "Read Alice's history", "conversation_id": conversation_id},
        )
        assert attack.status_code == 404
        assert len([row for row in fake_db.tables["chat_messages"] if row["conversation_id"] == conversation_id]) == 2
        assert client.get(f"/api/chat/conversations/{conversation_id}/messages", headers=bob).status_code == 404
    finally:
        app.dependency_overrides.pop(get_chat_orchestrator, None)


def test_guardian_persists_rule_evidence_to_originating_table(fake_db):
    client = TestClient(app)
    headers = _register(client, "guardian@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    today = date.today().isoformat()
    for index, amount in enumerate([100, 120, 80, 110, 90, 50000]):
        response = client.post(
            "/api/transactions/bank", headers=headers,
            json={"tx_date": today, "description": f"Transaction {index}", "amount": amount, "tx_type": "debit"},
        )
        assert response.status_code == 201, response.text
    result = run_guardian(user_id, fake_db)
    assert result["mode"] == "rule_based_insufficient_sample"
    assert result["anomaly_count"] == 1
    flagged = next(row for row in fake_db.tables["bank_transactions"] if row["is_anomaly"])
    assert flagged["amount"] == 50000
    assert flagged["anomaly_model_version"] == "guardian-large-amount-rule-v3"
    assert result["alerts"][0]["reason"]


def test_tax_agent_uses_transaction_lots_and_effective_dated_rules(fake_db):
    client = TestClient(app)
    headers = _register(client, "tax@example.com")
    user_id = fake_db.tables["users"][0]["user_id"]
    buy = client.post(
        "/api/transactions/equity", headers=headers,
        json={"tx_date": "2024-01-01", "tx_type": "buy", "symbol": "INFY", "quantity": 10, "price": 100},
    )
    sell = client.post(
        "/api/transactions/equity", headers=headers,
        json={"tx_date": "2025-08-01", "tx_type": "sell", "symbol": "INFY", "quantity": 10, "price": 200},
    )
    assert buy.status_code == sell.status_code == 201
    result = run_tax_agent(user_id, fake_db)
    assert result["status"] == "available"
    assert result["rule_version"] == "india-equity-tax-2024-07-23-v1"
    assert result["realized_gain_breakdown"][0]["ltcg"] == 1000
    assert result["realized_gain_breakdown"][0]["ltcg_exemption"] == 125000
    assert result["estimated_capital_gains_tax"] == 0
