"""Durable in-app notifications, preferences, redaction, and delivery state."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, time, timezone
from typing import Any
from uuid import uuid4

from repositories.base import SupabaseRepository

SEVERITY = {"info": 0, "warning": 1, "critical": 2}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)")
ACCOUNT_RE = re.compile(r"(?<!\d)\d{9,18}(?!\d)")
TOKEN_RE = re.compile(r"\b(?:Bearer\s+)?[A-Za-z0-9_-]{24,}\b", re.I)


def redact_outbound(value: str) -> str:
    redacted = EMAIL_RE.sub("[email redacted]", value)
    redacted = PAN_RE.sub("[tax identifier redacted]", redacted)
    redacted = PHONE_RE.sub("[phone redacted]", redacted)
    redacted = ACCOUNT_RE.sub("[account redacted]", redacted)
    return TOKEN_RE.sub("[secret redacted]", redacted)


class NotificationService:
    def __init__(self, db: Any):
        self.db = db
        self.repo = SupabaseRepository(db)

    def preferences(self, user_id: str) -> dict[str, Any]:
        rows = self.repo.list_for_user("notification_preferences", user_id, limit=1)
        if rows:
            return rows[0]
        result = self.db.table("notification_preferences").insert(
            {
                "notification_preference_id": str(uuid4()),
                "user_id": user_id,
                "in_app_enabled": True,
                "email_enabled": False,
                "minimum_severity": "info",
                "timezone": "Asia/Kolkata",
                "weekly_summary": True,
            }
        ).execute()
        return result.data[0]

    def update_preferences(self, user_id: str, values: dict[str, Any]) -> dict[str, Any]:
        current = self.preferences(user_id)
        payload = {**values, "updated_at": datetime.now(timezone.utc).isoformat()}
        result = self.db.table("notification_preferences").update(payload).eq(
            "notification_preference_id", current["notification_preference_id"]
        ).eq("user_id", user_id).execute()
        return result.data[0]

    def create(
        self,
        *,
        user_id: str,
        event_key: str,
        category: str,
        severity: str,
        title: str,
        body: str,
        evidence: dict[str, Any] | None = None,
        deep_link: str | None = None,
    ) -> dict[str, Any]:
        existing = self.repo.find("notifications", [("user_id", user_id), ("event_key", event_key)], limit=1)
        if existing:
            return existing[0]
        prefs = self.preferences(user_id)
        notification_id = str(uuid4())
        row = self.db.table("notifications").insert(
            {
                "notification_id": notification_id,
                "user_id": user_id,
                "event_key": event_key,
                "category": category,
                "severity": severity,
                "title": title[:160],
                "body": body[:1000],
                "evidence": evidence or {},
                "deep_link": deep_link,
            }
        ).execute().data[0]
        enabled = bool(prefs.get("in_app_enabled")) and SEVERITY[severity] >= SEVERITY[prefs["minimum_severity"]]
        self.db.table("notification_deliveries").insert(
            {
                "notification_delivery_id": str(uuid4()), "user_id": user_id,
                "notification_id": notification_id, "channel": "in_app",
                "status": "sent" if enabled else "suppressed",
                "sent_at": datetime.now(timezone.utc).isoformat() if enabled else None,
            }
        ).execute()
        if prefs.get("email_enabled"):
            self.db.table("notification_deliveries").insert(
                {
                    "notification_delivery_id": str(uuid4()), "user_id": user_id,
                    "notification_id": notification_id, "channel": "email", "status": "pending",
                }
            ).execute()
            from services.jobs import JobService

            JobService(self.db).enqueue_once("notification_delivery", user_id, {"notification_id": notification_id})
        return row

    def list(self, user_id: str, *, include_archived: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.repo.list_for_user("notifications", user_id, order_by="created_at", descending=True, limit=limit)
        return rows if include_archived else [row for row in rows if not row.get("archived_at")]

    def mark(self, notification_id: str, user_id: str, action: str) -> dict[str, Any]:
        fields = {"read": "read_at", "acknowledge": "acknowledged_at", "archive": "archived_at"}
        if action not in fields:
            raise ValueError("Unsupported notification action")
        result = self.db.table("notifications").update(
            {fields[action]: datetime.now(timezone.utc).isoformat()}
        ).eq("notification_id", notification_id).eq("user_id", user_id).execute()
        if not result.data:
            raise ValueError("Notification not found")
        return result.data[0]

    def email_payload(self, notification: dict[str, Any]) -> dict[str, str]:
        return {
            "subject": f"QUANT: {notification['severity'].title()} alert available",
            "body": redact_outbound(
                f"A new {notification['severity']} {notification['category']} alert is ready.\n\n"
                "Open QUANT to review the evidence. No account, holding, transaction, or tax details are included in this email."
            ),
        }

    def in_quiet_hours(self, preferences: dict[str, Any], local_time: time) -> bool:
        start_raw, end_raw = preferences.get("quiet_hours_start"), preferences.get("quiet_hours_end")
        if not start_raw or not end_raw:
            return False
        start = time.fromisoformat(str(start_raw))
        end = time.fromisoformat(str(end_raw))
        return start <= local_time < end if start < end else local_time >= start or local_time < end

    @staticmethod
    def delivery_fingerprint(payload: dict[str, str]) -> str:
        return hashlib.sha256(f"{payload['subject']}\n{payload['body']}".encode("utf-8")).hexdigest()
