# ADR 001: Structured agent communication and verification layers

Status: accepted for Phase 2.5

Specialists will exchange typed requests, claims, evidence references, conflicts, assumptions, and limitations through a bounded coordinator. They will not call one another recursively or negotiate through free-form prose.

All delivery pipelines share three responsibilities: a grounding layer before publication, a policy-driven arbitration layer for conflicts, and an outcome-evaluation layer after delivery. The evaluator records prediction/outcome comparisons and can propose calibration only when a defined target, labelled outcomes, minimum sample size, version, approval, and rollback plan exist. It never updates models or financial rules automatically.

This preserves the existing domain-agent names and deterministic services while making their purpose and trust boundaries explicit.
