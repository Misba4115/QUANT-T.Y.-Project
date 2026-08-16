"""Replay-safe deterministic Guardian evaluation for newly arriving events."""
from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.config import get_settings
from repositories.base import SupabaseRepository
from services.jobs import JobService
from services.notifications import NotificationService

RULE_VERSION = "guardian-rules-1.0.0"


def _number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


class GuardianStreamService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def ingest(
        self,
        *,
        user_id: str,
        event_id: str,
        asset_type: str,
        event_type: str,
        occurred_at: datetime,
        payload: dict[str, Any],
        enqueue: bool = True,
    ) -> dict[str, Any]:
        existing = self.repo.find("guardian_events", [("user_id", user_id), ("event_id", event_id)], limit=1)
        if existing:
            return {**existing[0], "duplicate": True}
        row = self.db.table("guardian_events").insert(
            {
                "guardian_event_id": str(uuid4()), "user_id": user_id, "event_id": event_id,
                "asset_type": asset_type, "event_type": event_type,
                "occurred_at": occurred_at.astimezone(timezone.utc).isoformat(),
                "payload": payload, "status": "pending",
            }
        ).execute().data[0]
        if enqueue:
            JobService(self.db).enqueue_once("guardian_events", user_id, {"event_id": event_id})
        return {**row, "duplicate": False}

    def process_pending(self, user_id: str | None = None) -> dict[str, Any]:
        query = self.db.table("guardian_events").select("*").eq("status", "pending")
        if user_id:
            query = query.eq("user_id", user_id)
        rows = query.execute().data or []
        rows.sort(key=lambda row: (str(row.get("occurred_at")), str(row.get("event_id"))))
        processed, alerts, failures = 0, 0, []
        for row in rows:
            try:
                created = self._evaluate(row)
                alerts += len(created)
                self.db.table("guardian_events").update(
                    {"status": "processed", "processed_at": datetime.now(timezone.utc).isoformat()}
                ).eq("guardian_event_id", row["guardian_event_id"]).eq("user_id", row["user_id"]).execute()
                processed += 1
            except Exception as exc:
                failures.append({"event_id": row["event_id"], "error": str(exc)[:240]})
                self.db.table("guardian_events").update({"status": "failed"}).eq(
                    "guardian_event_id", row["guardian_event_id"]
                ).eq("user_id", row["user_id"]).execute()
        status = "completed" if not failures else "partial" if processed else "failed"
        return {"status": status, "processed": processed, "alerts_created": alerts, "failures": failures}

    def alerts(self, user_id: str) -> list[dict[str, Any]]:
        return self.repo.list_for_user("guardian_alerts", user_id, order_by="created_at", descending=True)

    def feedback(self, user_id: str, alert_id: str, verdict: str, note: str | None) -> dict[str, Any]:
        alert = self.repo.get_for_user("guardian_alerts", alert_id, user_id)
        if not alert:
            raise ValueError("Guardian alert not found")
        rows = self.repo.find("guardian_feedback", [("user_id", user_id), ("guardian_alert_id", alert_id)], limit=1)
        payload = {"verdict": verdict, "note": note}
        if rows:
            return self.db.table("guardian_feedback").update(payload).eq(
                "guardian_feedback_id", rows[0]["guardian_feedback_id"]
            ).eq("user_id", user_id).execute().data[0]
        return self.db.table("guardian_feedback").insert(
            {
                "guardian_feedback_id": str(uuid4()), "user_id": user_id,
                "guardian_alert_id": alert_id, **payload,
            }
        ).execute().data[0]

    def _evaluate(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        payload = event["payload"]
        amount = _number(payload.get("amount") if "amount" in payload else payload.get("value"))
        quantity = _number(payload.get("quantity"))
        weight = _number(payload.get("portfolio_weight"))
        candidates: list[dict[str, Any]] = []
        if (amount is not None and amount < 0) or (quantity is not None and quantity < 0):
            candidates.append({
                "rule": "impossible-negative", "type": "data_quality", "severity": "critical",
                "title": "Impossible value detected", "explanation": "A new record contains a negative value where only non-negative values are valid.",
                "evidence": {"amount": amount, "quantity": quantity},
            })
        if weight is not None and weight > 0.35:
            candidates.append({
                "rule": "concentration-35", "type": "portfolio_risk", "severity": "warning",
                "title": "High portfolio concentration", "explanation": "The recorded instrument weight exceeds the 35% review threshold.",
                "evidence": {"observed_weight": weight, "threshold": 0.35},
            })
        baseline = self._baseline(event)
        if amount is not None and baseline:
            median, mad, sample_count = baseline
            robust_z = abs(amount - median) / max(1.4826 * mad, 1.0)
            if robust_z >= 4:
                candidates.append({
                    "rule": "amount-robust-z4", "type": "unusual_activity", "severity": "warning",
                    "title": "Unusual recorded amount", "explanation": "This value is far from the user's prior values for the same event type. It is unusual, not proof of fraud.",
                    "evidence": {"observed_amount": amount, "baseline_median": median, "robust_z": round(robust_z, 2), "sample_count": sample_count},
                })
        created = [self._store_alert(event, candidate) for candidate in candidates]
        return [row for row in created if row]

    def _baseline(self, event: dict[str, Any]) -> tuple[float, float, int] | None:
        rows = self.repo.find(
            "guardian_events",
            [("user_id", event["user_id"]), ("asset_type", event["asset_type"]), ("event_type", event["event_type"])],
        )
        occurred = datetime.fromisoformat(str(event["occurred_at"]).replace("Z", "+00:00"))
        values: list[float] = []
        for row in rows:
            row_time = datetime.fromisoformat(str(row["occurred_at"]).replace("Z", "+00:00"))
            if row["event_id"] == event["event_id"] or row_time > occurred:
                continue
            value = _number((row.get("payload") or {}).get("amount"))
            if value is not None and value >= 0:
                values.append(value)
        if len(values) < get_settings().guardian_min_history:
            return None
        median = statistics.median(values)
        mad = statistics.median(abs(value - median) for value in values)
        return median, mad, len(values)

    def _store_alert(self, event: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any] | None:
        cooldown_key = f"{event['event_id']}:{candidate['rule']}"
        existing = self.repo.find(
            "guardian_alerts",
            [("user_id", event["user_id"]), ("cooldown_key", cooldown_key), ("rule_version", RULE_VERSION)],
            limit=1,
        )
        if existing:
            return None
        row = self.db.table("guardian_alerts").insert(
            {
                "guardian_alert_id": str(uuid4()), "user_id": event["user_id"],
                "guardian_event_id": event["guardian_event_id"], "rule_version": RULE_VERSION,
                "alert_type": candidate["type"], "severity": candidate["severity"],
                "title": candidate["title"], "explanation": candidate["explanation"],
                "evidence": candidate["evidence"], "cooldown_key": cooldown_key,
            }
        ).execute().data[0]
        NotificationService(self.db).create(
            user_id=event["user_id"], event_key=f"guardian:{row['guardian_alert_id']}",
            category="guardian", severity=candidate["severity"], title=candidate["title"],
            body=candidate["explanation"], evidence={"guardian_alert_id": row["guardian_alert_id"]},
            deep_link="/guardian",
        )
        return row
