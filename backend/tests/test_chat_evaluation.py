import json
from pathlib import Path

from agents.intent_router import StructuredIntentRouter


def test_versioned_chat_evaluation_has_sixty_cases_and_meets_routing_gate():
    payload = json.loads((Path(__file__).parents[1] / "evaluations" / "chat_case_families.json").read_text())
    cases = [(family, text) for family in payload["families"] for text in family["paraphrases"]]
    assert payload["version"] == "phase-2.5-v1"
    assert len(cases) >= 60
    correct = 0
    for family, text in cases:
        decision = StructuredIntentRouter().route(text)
        correct += decision.primary_intent == family["expected"]
        if family["id"] == "recommendation":
            assert set(family["specialists"]) == set(decision.required_specialists)
    assert correct / len(cases) >= 0.90
