from datetime import datetime, timezone
from decimal import Decimal

from agents.consensus_arbiter import ConsensusArbiter
from agents.contracts import AgentClaim, AgentConflict, EvidenceRef, GroundingResult
from agents.grounding_checker import GroundingChecker

NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


def claim(claim_id="c1", **kwargs):
    return AgentClaim(
        claim_id=claim_id, agent=kwargs.pop("agent", "portfolio"), claim_type=kwargs.pop("claim_type", "fact"),
        subject=kwargs.pop("subject", "portfolio value"), statement=kwargs.pop("statement", "Portfolio value is 100 INR"),
        value=kwargs.pop("value", Decimal("100")), unit=kwargs.pop("unit", "currency"),
        evidence_ids=kwargs.pop("evidence_ids", ["e1"]), as_of=NOW, model_version="v1", **kwargs,
    )


def evidence(evidence_id="e1", **kwargs):
    return EvidenceRef(
        evidence_id=evidence_id, evidence_type=kwargs.pop("evidence_type", "private_record"),
        source_name=kwargs.pop("source_name", "holdings"), retrieved_at=NOW,
        observed_at=kwargs.pop("observed_at", NOW), value=kwargs.pop("value", Decimal("100")),
        unit=kwargs.pop("unit", "currency"), **kwargs,
    )


def test_number_mismatch_and_invented_evidence_are_rejected():
    checker = GroundingChecker()
    mismatch = checker.validate([claim()], [evidence(value=Decimal("90"))])[0]
    invented = checker.validate([claim(evidence_ids=["missing"])], [evidence()])[0]

    assert mismatch.outcome == "contradictory"
    assert "evidence_value_mismatch" in mismatch.reason_codes
    assert invented.outcome == "unsupported"
    assert invented.safe_statement is None


def test_calculation_recomputes_and_stale_market_evidence_is_visible():
    calculation = claim(claim_type="calculation", value=Decimal("30"), statement="Total is 30 INR")
    calc_evidence = evidence(value=Decimal("30"), metadata={"calculation": {"operation": "sum", "inputs": [10, 20]}})
    market_claim = claim(claim_id="market", subject="market price", evidence_ids=["m1"])
    market_evidence = evidence("m1", evidence_type="market_observation", source_name="provider-a", freshness="stale")

    results = GroundingChecker().validate([calculation, market_claim], [calc_evidence, market_evidence])

    assert results[0].outcome == "verified"
    assert results[1].outcome == "stale"


def test_public_support_effective_date_and_prompt_injection_are_checked():
    tax_claim = claim(subject="tax rate", statement="Tax rate is 10%", value=Decimal("10"), evidence_ids=["p1"])
    unsupported_source = evidence(
        "p1", evidence_type="public_source", source_name="official", value=Decimal("10"),
        metadata={"active": True, "authority": "CBDT", "effective_date": "2025-04-01", "supported_claim_ids": []},
    )
    injected_source = unsupported_source.model_copy(update={
        "evidence_id": "p2", "metadata": {**unsupported_source.metadata, "supported_claim_ids": ["injected"], "untrusted_instruction_detected": True}
    })
    injected_claim = tax_claim.model_copy(update={"claim_id": "injected", "evidence_ids": ["p2"]})

    results = GroundingChecker().validate([tax_claim, injected_claim], [unsupported_source, injected_source])

    assert results[0].outcome == "unsupported"
    assert "public_source_does_not_support_claim" in results[0].reason_codes
    assert results[1].outcome == "requires_review"


def test_arbiter_prefers_deterministic_newer_evidence_and_blocks_unsafe_cases():
    claims = [claim("calc", claim_type="calculation", evidence_ids=["calc-e"]), claim("model", claim_type="inference", evidence_ids=["model-e"])]
    refs = [
        evidence("calc-e", evidence_type="calculation", metadata={"calculation": {"operation": "sum", "inputs": [40, 60]}}),
        evidence("model-e", evidence_type="market_observation", source_name="provider-b"),
    ]
    grounding = [GroundingResult(claim_id=item.claim_id, outcome="verified") for item in claims]
    conflict = AgentConflict(conflict_id="x", claim_ids=["calc", "model"], conflict_type="provider_disagreement", subject="value")

    resolved = ConsensusArbiter().arbitrate(conflict, claims, refs, grounding)
    missing_lots = ConsensusArbiter().arbitrate(
        conflict.model_copy(update={"conflict_id": "tax", "conflict_type": "missing_tax_lots"}), claims, refs, grounding
    )

    assert resolved.status == "resolved" and resolved.winning_claim_id == "calc"
    assert missing_lots.status == "blocked"
    assert "sell" in missing_lots.prohibited_actions


def test_equal_grounded_agent_disagreement_remains_unresolved():
    claims = [claim("a", agent="tax", evidence_ids=["a-e"]), claim("b", agent="cashflow", evidence_ids=["b-e"])]
    refs = [evidence("a-e"), evidence("b-e")]
    grounding = [GroundingResult(claim_id="a", outcome="verified"), GroundingResult(claim_id="b", outcome="verified")]
    conflict = AgentConflict(conflict_id="x", claim_ids=["a", "b"], conflict_type="contradictory_claims", subject="action")

    result = ConsensusArbiter().arbitrate(conflict, claims, refs, grounding)

    assert result.status == "unresolved"
    assert result.winning_claim_id is None
