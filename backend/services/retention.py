"""Idempotent encrypted-ingestion object retention cleanup."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from services.inbox_ingestion import SupabaseEncryptedBlobStore


class RetentionCleanupService:
    def __init__(self, db, blob_store=None):
        self.db = db
        self.blob_store = blob_store or SupabaseEncryptedBlobStore(db)

    def run(self) -> dict:
        now = datetime.now(timezone.utc)
        rows = self.db.table("ingestion_messages").select("*").execute().data or []
        due = [row for row in rows if row.get("storage_key") and datetime.fromisoformat(str(row["purge_after"]).replace("Z", "+00:00")) <= now]
        attempts = []
        for row in due:
            key = row["storage_key"]
            attempt = {"message_id": row["ingestion_message_id"], "object_key_hash": hashlib.sha256(key.encode()).hexdigest(), "database_row_state":"due"}
            try:
                self.blob_store.delete(key)
                self.db.table("ingestion_messages").update({"storage_key": None}).eq("ingestion_message_id", row["ingestion_message_id"]).eq("user_id", row["user_id"]).execute()
                attempt.update(result="deleted", error_class=None)
            except Exception as exc:
                attempt.update(result="failed", error_class=type(exc).__name__)
            attempt["completed_at"] = datetime.now(timezone.utc).isoformat()
            attempts.append(attempt)
        deleted = sum(item["result"] == "deleted" for item in attempts)
        return {"status":"completed" if deleted == len(attempts) else "partial", "deleted":deleted, "attempts":attempts}
