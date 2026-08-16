"""Database-backed schedules and a separately executable worker."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any
from uuid import uuid4

from repositories.base import SupabaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def ensure_schedule(
        self, job_type: str, user_id: str | None, interval_seconds: int, config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        filters = [("job_type", job_type)]
        if user_id is not None:
            filters.append(("user_id", user_id))
        rows = self.repo.find("job_schedules", filters, limit=1)
        payload = {
            "job_type": job_type, "user_id": user_id, "enabled": True,
            "interval_seconds": max(60, interval_seconds), "config": config or {},
            "next_run_at": _utcnow().isoformat(), "updated_at": _utcnow().isoformat(),
        }
        if rows:
            return self.db.table("job_schedules").update(payload).eq(
                "job_schedule_id", rows[0]["job_schedule_id"]
            ).execute().data[0]
        payload["job_schedule_id"] = str(uuid4())
        return self.db.table("job_schedules").insert(payload).execute().data[0]

    def enqueue_once(
        self, job_type: str, user_id: str | None, config: dict[str, Any], delay_seconds: int = 0
    ) -> dict[str, Any]:
        nonce = str(uuid4())
        return self.db.table("job_schedules").insert(
            {
                "job_schedule_id": str(uuid4()), "user_id": user_id,
                "job_type": f"{job_type}:once:{nonce}", "enabled": True,
                "interval_seconds": 86_400, "next_run_at": (_utcnow() + timedelta(seconds=max(0, delay_seconds))).isoformat(),
                "config": {**config, "one_shot": nonce, "base_job_type": job_type},
            }
        ).execute().data[0]

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.repo.list_for_user("job_schedules", user_id, order_by="next_run_at")


class JobRunner:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def run_once(self, limit: int = 10) -> list[dict[str, Any]]:
        claimed = self.db.rpc("claim_due_job_schedules", {"p_limit": limit}).execute().data or []
        if not claimed:
            now = _utcnow()
            candidates = self.db.table("job_schedules").select("*").eq("enabled", True).execute().data or []
            claimed = [
                row for row in candidates
                if datetime.fromisoformat(str(row["next_run_at"]).replace("Z", "+00:00")) <= now
                and (not row.get("locked_until") or datetime.fromisoformat(str(row["locked_until"]).replace("Z", "+00:00")) < now)
            ][:limit]
        return [self._execute(schedule) for schedule in claimed]

    def _execute(self, schedule: dict[str, Any]) -> dict[str, Any]:
        due = str(schedule["next_run_at"])
        key = hashlib.sha256(f"{schedule['job_schedule_id']}:{due}".encode("utf-8")).hexdigest()
        existing = self.repo.find("job_runs", [("idempotency_key", key)], limit=1)
        if existing:
            return existing[0]
        run_id = str(uuid4())
        self.db.table("job_runs").insert(
            {
                "job_run_id": run_id, "user_id": schedule.get("user_id"),
                "job_schedule_id": schedule["job_schedule_id"], "job_type": schedule["job_type"],
                "idempotency_key": key, "status": "processing",
            }
        ).execute()
        status, result, error = "completed", None, None
        try:
            result = self._dispatch(schedule)
            if isinstance(result, dict) and result.get("status") in {"partial", "failed"}:
                status = result["status"]
        except Exception as exc:
            status, error = "failed", str(exc)[:500]
        now = _utcnow()
        run = self.db.table("job_runs").update(
            {"status": status, "result": result, "error": error, "completed_at": now.isoformat()}
        ).eq("job_run_id", run_id).execute().data[0]
        one_shot = bool((schedule.get("config") or {}).get("one_shot"))
        self.db.table("job_schedules").update(
            {
                "enabled": not one_shot,
                "last_run_at": now.isoformat(),
                "next_run_at": (now + timedelta(seconds=int(schedule["interval_seconds"]))).isoformat(),
                "locked_until": None,
                "updated_at": now.isoformat(),
            }
        ).eq("job_schedule_id", schedule["job_schedule_id"]).execute()
        return run

    def _dispatch(self, schedule: dict[str, Any]) -> dict[str, Any]:
        job_type = (schedule.get("config") or {}).get("base_job_type", schedule["job_type"])
        user_id = schedule.get("user_id")
        if job_type == "price_sync" and user_id:
            from services.market_data.service import MarketDataService
            config = schedule.get("config") or {}
            asset_types = None
            if config.get("respect_market_hours"):
                local = _utcnow().astimezone(ZoneInfo("Asia/Kolkata"))
                holiday = local.date().isoformat() in set(config.get("market_holidays") or [])
                market_open = local.weekday() < 5 and not holiday and (9, 0) <= (local.hour, local.minute) <= (16, 0)
                asset_types = None if market_open else {"Crypto"}
            return MarketDataService(self.db).refresh_user(user_id, asset_types=asset_types)
        if job_type == "guardian_events":
            from services.guardian_stream import GuardianStreamService

            return GuardianStreamService(self.db).process_pending(user_id=user_id)
        if job_type == "notification_delivery":
            from services.notification_delivery import NotificationDeliveryService

            return NotificationDeliveryService(self.db).process_pending(user_id=user_id)
        if job_type == "retention_cleanup":
            return {"status": "completed", "deleted": 0, "note": "Hosted retention cleanup requires storage adapter"}
        raise ValueError(f"Unsupported job type: {job_type}")
