"""Build an auditable fixture revision without changing the frozen v1 cases."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).parent
SOURCE = ROOT / "gc_sec_test_set.json"
TARGET = ROOT / "gc_sec_test_set_v2.json"
AS_OF = datetime(2026, 10, 21, tzinfo=timezone.utc)


def build() -> dict:
    source_bytes = SOURCE.read_bytes()
    data = json.loads(source_bytes)
    cases = {case["case_id"]: case for case in data["cases"]}
    assert len(cases) == len(data["cases"]) == 62

    data.pop("frozen_at", None)
    data["version"] = "2.0"
    data["revised_at"] = AS_OF.date().isoformat()
    data["derived_from_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    data["description"] = (
        "Revised controlled synthetic GC-SEC fixture. Evidence completeness and "
        "safety-oracle corrections were made after reviewing v1 failures; "
        "this is a development regression set, not an independent holdout."
    )
    data["categories"] = sorted({case["category"] for case in data["cases"]})
    data["revision_log"] = [
        "Give market observations explicit observation times and all evidence a fixed retrieval time; v1 adapter discarded observation times.",
        "TC_003 and TC_036 are source-supported facts/tolerance checks, not recomputable calculations.",
        "TC_048 and TC_049 now include illustrative calculation traces required for calculation claims.",
        "TC_017 blocks a claim with a phantom evidence ID instead of merely flagging it.",
        "TC_033 blocks an inactive tax source rather than marking it only stale.",
    ]

    for case in data["cases"]:
        case["claim"]["as_of"] = AS_OF.isoformat()
        if case.get("claim_b"):
            case["claim_b"]["as_of"] = AS_OF.isoformat()
        for evidence in case["evidence"]:
            evidence["retrieved_at"] = AS_OF.isoformat()
            if evidence["evidence_type"] == "market_observation":
                age_days = evidence.get("metadata", {}).get("age_days", 0)
                if evidence.get("freshness") == "stale" and not age_days:
                    age_days = max(case.get("freshness_window_days", 1) + 1, 2)
                evidence["observed_at"] = (AS_OF - timedelta(days=age_days)).isoformat()

    cases["TC_003"]["claim"]["claim_type"] = "fact"
    cases["TC_036"]["claim"]["claim_type"] = "fact"
    cases["TC_033"]["claim"]["claim_type"] = "fact"
    cases["TC_033"]["expected_grounding_outcome"] = "unsupported"
    cases["TC_033"]["expected_final_action"] = "block"
    cases["TC_017"]["expected_final_action"] = "block"

    calc_48 = next(e for e in cases["TC_048"]["evidence"] if e["evidence_id"] == "EV_TC048_CALC")
    calc_48["metadata"]["calculation"] = {"operation": "product", "inputs": [80000, "0.15"]}
    calc_49 = next(e for e in cases["TC_049"]["evidence"] if e["evidence_id"] == "EV_TC049_CALC")
    calc_49["metadata"]["calculation"] = {"operation": "ratio", "inputs": ["0.142", "0.1"]}

    TARGET.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    data = build()
    print(f"Wrote {TARGET.name}: {len(data['cases'])} cases, {len(data['categories'])} categories")
