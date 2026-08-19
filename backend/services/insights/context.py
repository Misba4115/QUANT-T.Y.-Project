"""Grounded Insights context without recommendation generation."""
from __future__ import annotations

from agents.context_assembler import UserFinancialContextAssembler
from agents.contracts import ContextRequirement, FULL_DECISION_CONTEXT


class InsightContextService:
    def __init__(self, db): self.db = db

    def build(self, user_id: str) -> dict:
        snapshot = UserFinancialContextAssembler(self.db).assemble(
            user_id, ContextRequirement(required_sections=set(FULL_DECISION_CONTEXT), financial_action=True)
        )
        counts = {name: len(rows) for name, rows in snapshot.sections.items()}
        observations = [
            {"code": f"{name}_records", "value": count, "evidence_scope": name}
            for name, count in sorted(counts.items()) if count
        ]
        return {
            "status": "available" if not snapshot.blockers else "insufficient_data",
            "context_version": snapshot.context_version,
            "data_as_of": snapshot.data_as_of.isoformat() if snapshot.data_as_of else None,
            "observations": observations,
            "blockers": snapshot.blockers,
            "required_user_decisions": [],
            "algorithm_status": "not_implemented",
            "recommendations": [],
            "evidence_count": len(snapshot.evidence),
        }
