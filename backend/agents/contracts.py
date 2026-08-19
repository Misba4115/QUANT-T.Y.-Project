"""Typed contracts shared by every Phase 2.5 intelligence pipeline."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.capabilities import CapabilityStatus, Freshness


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceRef(AgentContract):
    evidence_id: str
    evidence_type: Literal["private_record", "calculation", "market_observation", "public_source"]
    source_name: str
    record_locator: str | None = None
    observed_at: datetime | None = None
    retrieved_at: datetime
    freshness: Freshness = "unknown"
    content_hash: str | None = None
    value: Decimal | str | None = None
    unit: str | None = None
    currency: str | None = None
    aggregation_scope: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SafeError(AgentContract):
    code: str
    message: str
    retryable: bool = False


class AgentRequest(AgentContract):
    request_id: str
    requesting_agent: str
    requested_capability: str
    reason_code: str
    required_fields: list[str] = Field(default_factory=list)
    parent_claim_id: str | None = None


class AgentClaim(AgentContract):
    claim_id: str
    agent: str
    claim_type: Literal["fact", "calculation", "inference", "warning", "proposal"]
    subject: str
    statement: str
    value: Decimal | str | None = None
    unit: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    as_of: datetime
    model_version: str
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AgentResult(AgentContract):
    agent: str
    status: CapabilityStatus
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    claims: list[AgentClaim] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    requests: list[AgentRequest] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[SafeError] = Field(default_factory=list)


ContextSection = Literal[
    "profile",
    "goals",
    "risk",
    "cashflow",
    "holdings",
    "transactions",
    "guardian",
    "market",
    "conversation",
    "preferences",
]
FULL_DECISION_CONTEXT: frozenset[ContextSection] = frozenset(
    {"profile", "goals", "risk", "cashflow", "holdings", "transactions", "guardian", "market", "preferences"}
)


class ContextRequirement(AgentContract):
    required_sections: set[ContextSection] = Field(default_factory=set)
    financial_action: bool = False
    max_records_per_section: int = Field(default=100, ge=1, le=500)
    max_serialized_chars: int = Field(default=60_000, ge=1_000, le=250_000)

    @model_validator(mode="after")
    def require_full_decision_context(self):
        if self.financial_action:
            self.required_sections.update(FULL_DECISION_CONTEXT)
        return self


class ContextSnapshot(AgentContract):
    context_version: str
    user_id: str = Field(exclude=True)
    assembled_at: datetime
    data_as_of: datetime | None = None
    requirement: ContextRequirement
    sections: dict[str, list[dict[str, Any]]]
    evidence: list[EvidenceRef]
    missing_context_codes: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    compacted: bool = False


PrimaryIntent = Literal[
    "informational_education",
    "user_specific_analysis",
    "cross_domain_analysis",
    "recommendation_like",
    "unsupported",
    "clarification",
]


class IntentDecision(AgentContract):
    primary_intent: PrimaryIntent
    secondary_intents: list[str] = Field(default_factory=list)
    required_specialists: list[Literal["guardian", "portfolio", "tax", "cashflow"]] = Field(default_factory=list)
    required_private_contexts: set[ContextSection] = Field(default_factory=set)
    requires_public_knowledge: bool = False
    risk_level: Literal["low", "medium", "high"] = "low"
    clarification_required: bool = False
    confidence: float = Field(ge=0, le=1)
    route_source: Literal["semantic_model", "deterministic_fallback"]


class RunTraceEvent(AgentContract):
    sequence: int = Field(ge=0)
    event: str
    capability: str | None = None
    status: str
    detail: str | None = None


GroundingOutcome = Literal[
    "verified", "verified_with_limitations", "unsupported", "contradictory", "stale", "requires_review"
]


class GroundingResult(AgentContract):
    claim_id: str
    outcome: GroundingOutcome
    reason_codes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    safe_statement: str | None = None


class AgentConflict(AgentContract):
    conflict_id: str
    claim_ids: list[str] = Field(min_length=2)
    conflict_type: Literal["contradictory_claims", "provider_disagreement", "constraint_interaction", "missing_tax_lots"]
    subject: str
    material: bool = True


class ArbitrationResult(AgentContract):
    conflict_id: str
    status: Literal["resolved", "unresolved", "blocked"]
    winning_claim_id: str | None = None
    reason_code: str
    user_message: str
    prohibited_actions: list[str] = Field(default_factory=list)
    policy_version: str = "consensus-policy-v1"
