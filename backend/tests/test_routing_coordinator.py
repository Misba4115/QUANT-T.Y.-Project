from agents.coordinator import AgentCoordinator
from agents.intent_router import StructuredIntentRouter


def test_paraphrases_route_without_exact_legacy_keywords():
    router = StructuredIntentRouter()

    affordability = router.route("Could my monthly runway support a home deposit?")
    exposure = router.route("Am I too exposed to one company?")
    cross_domain = router.route("How would redeeming this affect what I owe and my emergency fund?")

    assert affordability.required_specialists == ["cashflow"]
    assert exposure.required_specialists == ["portfolio"]
    assert set(cross_domain.required_specialists) == {"tax", "cashflow"}
    assert cross_domain.primary_intent == "cross_domain_analysis"


def test_recommendation_like_route_requires_full_decision_team_and_context():
    decision = StructuredIntentRouter().route("What should I sell and where should I invest the proceeds?")

    assert decision.primary_intent == "recommendation_like"
    assert decision.risk_level == "high"
    assert decision.required_specialists == ["guardian", "portfolio", "tax", "cashflow"]
    assert {"goals", "risk", "cashflow", "holdings", "transactions"}.issubset(decision.required_private_contexts)


def test_semantic_router_falls_back_when_model_contract_is_invalid():
    decision = StructuredIntentRouter(lambda _message: "not json").route("Is my asset mix concentrated?")

    assert decision.route_source == "deterministic_fallback"
    assert decision.required_specialists == ["portfolio"]


def test_underspecified_followup_requests_clarification():
    router = StructuredIntentRouter()
    assert router.route("Is that normal?").primary_intent == "clarification"
    assert router.route("What about last month?").primary_intent == "clarification"
    assert router.route("What is the situation with my account?").primary_intent == "clarification"
    assert router.route("Explain current tax guidance").primary_intent == "informational_education"


def test_coordinator_bounds_deduplicates_and_rejects_recursive_requests(fake_db):
    calls = []

    def portfolio(_user_id, _db):
        calls.append("portfolio")
        request = {
            "request_id": "req-1", "requesting_agent": "portfolio", "requested_capability": "tax",
            "reason_code": "tax_impact", "required_fields": ["lots"],
        }
        return {"status": "available", "requests": [request, request]}

    def tax(_user_id, _db):
        calls.append("tax")
        return {
            "status": "partial",
            "requests": [{
                "request_id": "req-2", "requesting_agent": "tax", "requested_capability": "tax",
                "reason_code": "recursive", "required_fields": [],
            }],
        }

    coordinator = AgentCoordinator(fake_db, {"portfolio": portfolio, "tax": tax}, max_follow_up_rounds=2)
    outputs, errors, trace = coordinator.execute("alice", ["portfolio"])

    assert calls == ["portfolio", "tax"]
    assert set(outputs) == {"portfolio", "tax"}
    assert sum(item["event"] == "follow_up_authorized" for item in trace) == 1
    assert any(item["code"] == "recursive_self_request" for item in errors)


def test_coordinator_keeps_failures_partial_and_traceable(fake_db):
    def broken(_user_id, _db):
        raise RuntimeError("private provider detail")

    outputs, errors, trace = AgentCoordinator(fake_db, {"tax": broken}).execute("alice", ["tax"])

    assert outputs == {}
    assert errors == [{"node": "tax", "code": "RuntimeError"}]
    assert trace[0]["event"] == "agent_failed"
    assert "private provider detail" not in str(trace)
