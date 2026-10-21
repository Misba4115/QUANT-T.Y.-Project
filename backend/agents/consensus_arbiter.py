"""Explicit, non-voting conflict policies over already-grounded claims."""
from __future__ import annotations

from agents.contracts import AgentClaim, AgentConflict, ArbitrationResult, EvidenceRef, GroundingResult


VALID_GROUNDING = {"verified", "verified_with_limitations", "stale"}
EVIDENCE_RANK = {"calculation": 4, "private_record": 3, "market_observation": 2, "public_source": 1}


class ConsensusArbiter:
    def arbitrate(
        self,
        conflict: AgentConflict,
        claims: list[AgentClaim],
        evidence: list[EvidenceRef],
        grounding: list[GroundingResult],
    ) -> ArbitrationResult:
        claim_map = {item.claim_id: item for item in claims}
        evidence_map = {item.evidence_id: item for item in evidence}
        grounding_map = {item.claim_id: item for item in grounding}
        relevant = [claim_map[item] for item in conflict.claim_ids if item in claim_map]

        if conflict.conflict_type == "missing_tax_lots":
            return self._blocked(conflict, "missing_acquisition_history", "Exact tax impact cannot be determined without acquisition lots.")
        if any(item.claim_type == "proposal" for item in relevant):
            return self._blocked(conflict, "phase_2_5_action_prohibited", "The constraints can be explained, but no investment action is approved.")
        valid = [item for item in relevant if grounding_map.get(item.claim_id) and grounding_map[item.claim_id].outcome in VALID_GROUNDING]
        if not valid:
            return self._blocked(conflict, "no_grounded_claim", "The conflict remains unresolved because no claim passed grounding.")

        scored = []
        for claim in valid:
            refs = [evidence_map[item] for item in claim.evidence_ids if item in evidence_map]
            rank = max((EVIDENCE_RANK.get(item.evidence_type, 0) for item in refs), default=0)
            newest = max((item.observed_at.timestamp() for item in refs if item.observed_at), default=0)
            stale_penalty = any(item.freshness == "stale" for item in refs)
            # A stale source must not outrank a fresh source solely by type.
            scored.append(((not stale_penalty, rank, newest), claim))
        scored.sort(key=lambda item: item[0], reverse=True)
        if len(scored) > 1 and scored[0][0] == scored[1][0]:
            return self._blocked(conflict, "material_conflict_unresolved", "Grounded sources disagree materially; user clarification or newer evidence is required.")
        winner = scored[0][1]
        return ArbitrationResult(
            conflict_id=conflict.conflict_id,
            status="resolved",
            winning_claim_id=winner.claim_id,
            reason_code="higher_priority_grounded_evidence",
            user_message="The higher-priority, newer grounded evidence was selected while retaining the conflicting claim in the audit record.",
        )

    @staticmethod
    def _blocked(conflict: AgentConflict, reason: str, message: str) -> ArbitrationResult:
        return ArbitrationResult(
            conflict_id=conflict.conflict_id,
            status="blocked" if reason in {"missing_acquisition_history", "phase_2_5_action_prohibited"} else "unresolved",
            reason_code=reason,
            user_message=message,
            prohibited_actions=["buy", "sell", "rebalance", "execute_trade"],
        )
