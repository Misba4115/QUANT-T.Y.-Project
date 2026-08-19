"""Versioned capability truth and shared availability vocabulary."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.config import Settings


CapabilityStatus = Literal[
    "available",
    "partial",
    "insufficient_data",
    "stale",
    "not_configured",
    "provider_unavailable",
    "experimental",
    "not_implemented",
    "failed",
]
Freshness = Literal["fresh", "delayed", "stale", "unknown"]

STATUS_VOCABULARY: tuple[str, ...] = (
    "available",
    "partial",
    "insufficient_data",
    "stale",
    "not_configured",
    "provider_unavailable",
    "experimental",
    "not_implemented",
    "failed",
)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapabilityRecord(ContractModel):
    capability_id: str
    status: CapabilityStatus
    reason_code: str
    detail: str
    configured: bool
    data_as_of: datetime | None = None
    source: str | None = None
    freshness: Freshness = "unknown"
    sample_count: int | None = Field(default=None, ge=0)
    retryable: bool = False


class IntelligenceLayer(ContractModel):
    layer: int = Field(ge=1, le=3)
    capability_id: str
    purpose: str
    accepts: list[str]
    emits: list[str]
    mutation_policy: str


class CapabilityRegistry(ContractModel):
    contract_version: str
    generated_at: datetime
    status_vocabulary: tuple[str, ...]
    capabilities: dict[str, CapabilityRecord]
    intelligence_layers: list[IntelligenceLayer]


def _configured(
    capability_id: str,
    configured: bool,
    *,
    detail: str,
    source: str,
    configured_status: CapabilityStatus = "partial",
    configured_reason: str = "live_probe_required",
) -> CapabilityRecord:
    return CapabilityRecord(
        capability_id=capability_id,
        status=configured_status if configured else "not_configured",
        reason_code=configured_reason if configured else "missing_configuration",
        detail=detail,
        configured=configured,
        source=source,
        retryable=configured,
    )


def build_capability_registry(settings: Settings) -> CapabilityRegistry:
    """Return declared capability truth without treating configuration as health."""
    generated_at = datetime.now(timezone.utc)
    llm_configured = bool(
        settings.gemini_api_key if settings.llm_provider == "gemini" else settings.openai_api_key
    )
    smtp_configured = bool(settings.smtp_host and settings.smtp_from_email)
    capabilities = {
        "database": _configured(
            "database",
            settings.database_configured,
            detail="Supabase runtime database; readiness performs a live schema probe",
            source="supabase",
        ),
        "llm": _configured(
            "llm",
            llm_configured,
            detail="Configured chat provider; structured-output health is not yet live-probed",
            source=settings.llm_provider,
        ),
        "qdrant": _configured(
            "qdrant",
            bool(settings.qdrant_url),
            detail="Public knowledge vector store; URL configuration does not prove collection readiness",
            source="qdrant",
        ),
        "market_data": CapabilityRecord(
            capability_id="market_data",
            status="experimental",
            reason_code="uncontracted_public_adapters",
            detail="Yahoo Finance, AMFI, and CoinGecko adapters are independently degradable",
            configured=True,
            source="yahoo_finance,amfi,coingecko",
            retryable=True,
        ),
        "worker": CapabilityRecord(
            capability_id="worker",
            status="partial",
            reason_code="activity_probe_requires_database",
            detail="Worker execution, leases, retries, and retention cleanup exist; live activity requires the database readiness probe",
            configured=True,
            source="database_job_runner",
            retryable=True,
        ),
        "smtp": _configured(
            "smtp",
            smtp_configured,
            detail="Optional outbound email delivery",
            source="smtp",
        ),
        "upstox": _configured(
            "upstox",
            bool(settings.upstox_client_id and settings.upstox_client_secret),
            detail="Optional read-only broker connector",
            source="upstox",
        ),
        "ingestion_inbox": _configured(
            "ingestion_inbox",
            bool(settings.inbox_webhook_secret),
            detail="Optional forwarding inbox webhook",
            source="signed_webhook",
        ),
        "parsers": CapabilityRecord(
            capability_id="parsers",
            status="partial",
            reason_code="verified_generic_layouts_only",
            detail="Golden-tested generic CSV/XLSX and text-based CAS families; provider-specific layouts are not advertised without approved samples",
            configured=True,
            source="local_parser_registry",
        ),
        "insights": CapabilityRecord(
            capability_id="insights",
            status="partial",
            reason_code="readiness_only_algorithm_deferred",
            detail="Grounded context/readiness is available; recommendation generation is intentionally not implemented",
            configured=True,
            source="phase_2_5_plan",
        ),
        "grounding_checker": CapabilityRecord(
            capability_id="grounding_checker",
            status="available",
            reason_code="deterministic_evidence_validation",
            detail="Validates typed claims and filters unsupported material figures before delivery",
            configured=True,
            source="intelligence_runtime",
        ),
        "consensus_arbiter": CapabilityRecord(
            capability_id="consensus_arbiter",
            status="available",
            reason_code="versioned_constraint_policy",
            detail="Reconciles grounded conflicts using explicit non-voting policies",
            configured=True,
            source="intelligence_runtime",
        ),
        "outcome_evaluator": CapabilityRecord(
            capability_id="outcome_evaluator",
            status="available",
            reason_code="observational_evaluation_only",
            detail="Compares versioned predictions with labelled outcomes without automatic mutation",
            configured=True,
            source="intelligence_runtime",
        ),
    }
    layers = [
        IntelligenceLayer(
            layer=1,
            capability_id="grounding_checker",
            purpose="Validate every material specialist claim against tool or source evidence",
            accepts=["agent_claims", "evidence_refs", "calculation_traces"],
            emits=["grounding_results", "rejected_claims", "limitations"],
            mutation_policy="May reject or qualify claims; cannot alter source data",
        ),
        IntelligenceLayer(
            layer=2,
            capability_id="consensus_arbiter",
            purpose="Resolve cross-domain conflicts by documented constraint priority",
            accepts=["grounded_claims", "detected_conflicts", "policy_version"],
            emits=["resolved_conflicts", "unresolved_conflicts", "safe_output_constraints"],
            mutation_policy="May constrain output; cannot invent evidence or authorize financial actions",
        ),
        IntelligenceLayer(
            layer=3,
            capability_id="outcome_evaluator",
            purpose="Measure delivered predictions against labelled realized outcomes",
            accepts=["delivered_output_refs", "labelled_outcomes", "evaluation_target"],
            emits=["evaluation_metrics", "calibration_proposals", "drift_signals"],
            mutation_policy="May propose versioned recalibration only; never changes a model or rule automatically",
        ),
    ]
    return CapabilityRegistry(
        contract_version="2.5.0",
        generated_at=generated_at,
        status_vocabulary=STATUS_VOCABULARY,
        capabilities=capabilities,
        intelligence_layers=layers,
    )


def legacy_readiness_status(status: CapabilityStatus) -> str:
    """Preserve the pre-2.5 readiness field while clients adopt capability_status."""
    if status == "available":
        return "ready"
    if status in {"not_configured", "not_implemented"}:
        return "unavailable"
    if status in {"failed", "provider_unavailable"}:
        return "error"
    return "configured"
