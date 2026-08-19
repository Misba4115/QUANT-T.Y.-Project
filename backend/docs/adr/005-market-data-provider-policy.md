# ADR 005: Treat market providers as explicit, degradable dependencies

Status: accepted for Phase 2.5

Every market observation identifies its provider, observation time, retrieval time, and freshness. Configuration is not readiness. Provider selection, fallback, rate limiting, circuit breaking, and last-known-good behavior are policy decisions with measurable health.

Public adapters remain experimental until contractual, licensing, freshness, and reliability requirements are documented and tested.
