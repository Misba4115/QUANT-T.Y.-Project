# Phase 2.5 capability contract

Contract version: `2.5.0`

`GET /api/capabilities/` is the canonical, credential-free feature registry. A configured URL or key never proves that a dependency is operational. `GET /api/readiness` therefore retains its legacy `status` field and adds `capability_status`, `reason_code`, `data_as_of`, `source`, `freshness`, `sample_count`, and `retryable`.

Canonical statuses are `available`, `partial`, `insufficient_data`, `stale`, `not_configured`, `provider_unavailable`, `experimental`, `not_implemented`, and `failed`.

The registry also freezes the three shared intelligence responsibilities without renaming domain agents:

1. Grounding validates claims and calculations against evidence.
2. Arbitration reconciles only grounded cross-domain conflicts by policy.
3. Outcome evaluation compares delivered outputs with labelled realized outcomes and may emit calibration proposals. It cannot mutate a financial model, rule, or policy automatically.

The endpoint contains configuration truth only and never returns credentials.
