"""Observational outcome evaluation with no automatic model mutation."""
from __future__ import annotations

from statistics import mean


class OutcomeEvaluator:
    def evaluate(self, predictions: list[dict], *, target_version: str, minimum_sample_size: int = 30) -> dict:
        labelled = [row for row in predictions if row.get("predicted") is not None and row.get("realized") is not None]
        errors = [abs(float(row["predicted"]) - float(row["realized"])) for row in labelled]
        sample_count = len(errors)
        metrics = {"mean_absolute_error": mean(errors) if errors else None}
        eligible = sample_count >= minimum_sample_size
        return {
            "target_version": target_version,
            "sample_count": sample_count,
            "metrics": metrics,
            "status": "review_required" if eligible else "observed",
            "calibration_proposal": {"reason":"measured_error","requires_approval":True,"rollback_required":True} if eligible else None,
            "automatic_mutation": False,
        }
