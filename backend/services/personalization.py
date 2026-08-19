"""Versioned, reviewable risk dimensions and presentation-only personas."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from repositories.base import SupabaseRepository

RISK_MODEL_VERSION = "risk-dimensions-1.0.0"


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


class PersonalizationService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def assess(self, user_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        missing = [key for key, value in inputs.items() if value is None]
        loss = float(inputs.get("loss_tolerance") or 0) / 4 * 100
        emergency = _clamp(float(inputs.get("emergency_months") or 0) / 12 * 100)
        horizon = _clamp(float(inputs.get("time_horizon_years") or 0) / 15 * 100)
        stability = float(inputs.get("income_stability") or 0) / 4 * 100
        liability = (1 - float(inputs.get("liability_ratio") or 0)) * 100
        concentration = (1 - float(inputs.get("concentration_ratio") or 0)) * 100
        liquidity = (1 - float(inputs.get("illiquid_ratio") or 0)) * 100
        knowledge = float(inputs.get("knowledge_level") or 0) / 4 * 100
        dimensions = {
            "tolerance": round(loss, 4),
            "loss_capacity": round((emergency * 0.45 + stability * 0.30 + liability * 0.25), 4),
            "goal_horizon": round(horizon, 4),
            "portfolio_resilience": round((concentration * 0.55 + liquidity * 0.45), 4),
            "experience": round(knowledge, 4),
        }
        overall = round(
            dimensions["tolerance"] * 0.25 + dimensions["loss_capacity"] * 0.30
            + dimensions["goal_horizon"] * 0.20 + dimensions["portfolio_resilience"] * 0.20
            + dimensions["experience"] * 0.05,
            4,
        )
        uncertainty = round(len(missing) / max(len(inputs), 1), 4)
        row = self.db.table("risk_assessments").insert(
            {
                "risk_assessment_id": str(uuid4()), "user_id": user_id,
                "model_version": RISK_MODEL_VERSION, "inputs": inputs, "dimensions": dimensions,
                "overall_score": overall, "uncertainty": uncertainty,
            }
        ).execute().data[0]
        return {**row, "label": "conservative" if overall < 40 else "balanced" if overall < 70 else "growth"}

    def latest_assessment(self, user_id: str) -> dict[str, Any] | None:
        rows = self.repo.list_for_user("risk_assessments", user_id, order_by="assessed_at", descending=True, limit=1)
        return rows[0] if rows else None

    def preferences(self, user_id: str) -> dict[str, Any]:
        rows = self.repo.list_for_user("user_preferences", user_id, limit=1)
        if rows:
            return rows[0]
        return self.db.table("user_preferences").insert(
            {
                "user_preference_id": str(uuid4()), "user_id": user_id,
                "persona": "guided", "explanation_depth": "balanced",
                "dashboard_emphasis": [], "explicit_feedback": {},
            }
        ).execute().data[0]

    def update_preferences(self, user_id: str, values: dict[str, Any]) -> dict[str, Any]:
        current = self.preferences(user_id)
        return self.db.table("user_preferences").update(
            {**values, "updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_preference_id", current["user_preference_id"]).eq("user_id", user_id).execute().data[0]

    def reset_preferences(self, user_id: str) -> dict[str, Any]:
        return self.update_preferences(
            user_id,
            {"persona": "guided", "explanation_depth": "balanced", "dashboard_emphasis": [], "explicit_feedback": {}},
        )
