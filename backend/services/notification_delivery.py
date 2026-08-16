"""Redacted SMTP delivery with retry and dead-letter state."""
from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from core.config import get_settings
from repositories.base import SupabaseRepository
from services.notifications import NotificationService


class EmailAdapter(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...


class SMTPEmailAdapter:
    def __init__(self):
        self.settings = get_settings()

    def send(self, recipient: str, subject: str, body: str) -> None:
        settings = self.settings
        if not settings.smtp_host or not settings.smtp_from_email:
            raise RuntimeError("SMTP email delivery is not configured")
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = settings.smtp_from_email, recipient, subject
        message.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)


class NotificationDeliveryService:
    def __init__(self, db: Any, email_adapter: EmailAdapter | None = None):
        self.db = db
        self.repo = SupabaseRepository(db)
        self.email_adapter = email_adapter or SMTPEmailAdapter()

    def process_pending(self, user_id: str | None = None) -> dict[str, Any]:
        query = self.db.table("notification_deliveries").select("*").eq("status", "pending").eq("channel", "email")
        if user_id:
            query = query.eq("user_id", user_id)
        rows = query.execute().data or []
        sent, suppressed, failed = 0, 0, 0
        for delivery in rows:
            notification = self.repo.get_for_user("notifications", delivery["notification_id"], delivery["user_id"])
            users = self.repo.find("users", [("user_id", delivery["user_id"])], limit=1)
            if not notification or not users:
                self._finish(delivery, "dead_letter", "Notification or recipient no longer exists")
                failed += 1
                continue
            prefs = NotificationService(self.db).preferences(delivery["user_id"])
            local_now = datetime.now(timezone.utc).astimezone(ZoneInfo(str(prefs.get("timezone") or "Asia/Kolkata")))
            if NotificationService(self.db).in_quiet_hours(prefs, local_now.time()):
                self._finish(delivery, "suppressed", "Suppressed by quiet hours")
                suppressed += 1
                continue
            payload = NotificationService(self.db).email_payload(notification)
            attempts = int(delivery.get("attempt_count") or 0) + 1
            try:
                self.email_adapter.send(str(users[0]["email"]), payload["subject"], payload["body"])
                self.db.table("notification_deliveries").update(
                    {"status": "sent", "attempt_count": attempts, "sent_at": datetime.now(timezone.utc).isoformat(), "last_error": None}
                ).eq("notification_delivery_id", delivery["notification_delivery_id"]).eq("user_id", delivery["user_id"]).execute()
                sent += 1
            except Exception as exc:
                terminal = attempts >= 5
                self.db.table("notification_deliveries").update(
                    {"status": "dead_letter" if terminal else "pending", "attempt_count": attempts, "last_error": str(exc)[:240]}
                ).eq("notification_delivery_id", delivery["notification_delivery_id"]).eq("user_id", delivery["user_id"]).execute()
                if not terminal:
                    from services.jobs import JobService

                    JobService(self.db).enqueue_once(
                        "notification_delivery", delivery["user_id"],
                        {"notification_delivery_id": delivery["notification_delivery_id"]},
                        delay_seconds=min(60 * (2 ** (attempts - 1)), 3600),
                    )
                failed += 1
        status = "completed" if not failed else "partial" if sent or suppressed else "failed"
        return {"status": status, "sent": sent, "suppressed": suppressed, "failed": failed}

    def _finish(self, delivery: dict[str, Any], status: str, error: str) -> None:
        self.db.table("notification_deliveries").update(
            {"status": status, "last_error": error, "attempt_count": int(delivery.get("attempt_count") or 0) + 1}
        ).eq("notification_delivery_id", delivery["notification_delivery_id"]).eq("user_id", delivery["user_id"]).execute()
