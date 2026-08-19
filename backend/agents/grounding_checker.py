"""Deterministic claim grounding; semantic evaluation can only add limitations."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Callable

from agents.contracts import AgentClaim, EvidenceRef, GroundingResult

NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?")


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("%", ""))
    except (InvalidOperation, ValueError):
        return None


class GroundingChecker:
    def __init__(self, semantic_evaluator: Callable[[AgentClaim, list[EvidenceRef]], bool] | None = None):
        self.semantic_evaluator = semantic_evaluator

    def validate(self, claims: list[AgentClaim], evidence: list[EvidenceRef]) -> list[GroundingResult]:
        registry = {item.evidence_id: item for item in evidence}
        return [self._validate_claim(claim, registry) for claim in claims]

    def _validate_claim(self, claim: AgentClaim, registry: dict[str, EvidenceRef]) -> GroundingResult:
        reasons: list[str] = []
        refs = [registry[item] for item in claim.evidence_ids if item in registry]
        missing_ids = [item for item in claim.evidence_ids if item not in registry]
        numerical = claim.value is not None or bool(NUMBER_RE.search(claim.statement))

        if missing_ids:
            reasons.append("unknown_evidence_id")
        if numerical and not claim.evidence_ids:
            reasons.append("numerical_claim_without_evidence")
        if numerical and not refs:
            reasons.append("numerical_claim_unrecomputable")
        if any(item.metadata.get("untrusted_instruction_detected") for item in refs):
            return self._result(claim, "requires_review", [*reasons, "untrusted_document_instruction"])
        if missing_ids or (numerical and not refs):
            return self._result(claim, "unsupported", reasons)

        claim_value = _decimal(claim.value)
        evidence_values = [_decimal(item.value) for item in refs if item.value is not None]
        if claim_value is not None and evidence_values and all(value != claim_value for value in evidence_values):
            reasons.append("evidence_value_mismatch")
        if claim.unit and any(item.unit and item.unit != claim.unit for item in refs):
            reasons.append("unit_mismatch")
        claim_currency = next((item.metadata.get("currency") for item in refs if item.metadata.get("claim_currency")), None)
        if claim_currency and any(item.currency and item.currency != claim_currency for item in refs):
            reasons.append("currency_mismatch")
        if claim.claim_type == "calculation" and not self._recomputes(claim, refs):
            reasons.append("calculation_mismatch")
        if self._is_market_claim(claim) and any(
            item.evidence_type != "market_observation" or not item.source_name or item.observed_at is None for item in refs
        ):
            reasons.append("market_provenance_incomplete")
        if self._is_tax_claim(claim) and any(
            item.evidence_type == "public_source" and (
                not item.metadata.get("active") or not item.metadata.get("effective_date") or not item.metadata.get("authority")
            ) for item in refs
        ):
            reasons.append("authoritative_source_inactive_or_undated")
        if any(item.evidence_type == "public_source" and claim.claim_id not in item.metadata.get("supported_claim_ids", []) for item in refs):
            reasons.append("public_source_does_not_support_claim")
        if reasons:
            outcome = "contradictory" if any(code.endswith("mismatch") for code in reasons) else "unsupported"
            return self._result(claim, outcome, reasons)
        if any(item.freshness == "stale" for item in refs):
            return self._result(claim, "stale", ["stale_evidence"])
        if self.semantic_evaluator is not None and not self.semantic_evaluator(claim, refs):
            return self._result(claim, "verified_with_limitations", ["semantic_support_uncertain"])
        if claim.limitations:
            return self._result(claim, "verified_with_limitations", ["claim_has_limitations"], safe_statement=claim.statement)
        return self._result(claim, "verified", [], safe_statement=claim.statement)

    @staticmethod
    def _recomputes(claim: AgentClaim, refs: list[EvidenceRef]) -> bool:
        trace = next((item.metadata.get("calculation") for item in refs if item.metadata.get("calculation")), None)
        if trace is None:
            return False
        inputs = [_decimal(value) for value in trace.get("inputs", [])]
        if any(value is None for value in inputs):
            return False
        operation = trace.get("operation")
        if operation == "sum":
            computed = sum(inputs, Decimal("0"))
        elif operation == "difference" and len(inputs) == 2:
            computed = inputs[0] - inputs[1]
        elif operation == "product":
            computed = Decimal("1")
            for value in inputs:
                computed *= value
        else:
            return False
        return computed == _decimal(claim.value)

    @staticmethod
    def _is_market_claim(claim: AgentClaim) -> bool:
        return any(word in claim.subject.lower() for word in ("price", "market", "return", "nav"))

    @staticmethod
    def _is_tax_claim(claim: AgentClaim) -> bool:
        return "tax" in claim.subject.lower() or "tax" in claim.statement.lower()

    @staticmethod
    def _result(claim: AgentClaim, outcome: str, reasons: list[str], safe_statement: str | None = None) -> GroundingResult:
        return GroundingResult(
            claim_id=claim.claim_id,
            outcome=outcome,
            reason_codes=list(dict.fromkeys(reasons)),
            evidence_ids=claim.evidence_ids,
            safe_statement=safe_statement,
        )
