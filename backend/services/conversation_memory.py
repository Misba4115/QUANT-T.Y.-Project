"""Deterministic private conversation summaries; never uses the public vector store."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4


class ConversationMemoryService:
    VERSION = "conversation-summary-v1"

    def __init__(self, db): self.db = db

    def update(self, user_id: str, conversation_id: str, messages: list[dict]) -> dict | None:
        if len(messages) <= 8:
            return None
        safe = [f"{row['role']}: {' '.join(str(row['content']).split())[:400]}" for row in messages[:-6]]
        summary = "\n".join(safe)[-6000:]
        digest = hashlib.sha256(summary.encode()).hexdigest()
        existing = self.db.table("conversation_summaries").select("*").eq("conversation_id", conversation_id).eq("user_id", user_id).limit(1).execute().data or []
        payload = {"summary": summary, "summary_version": self.VERSION, "message_count": len(messages), "content_hash": digest, "updated_at": datetime.now(timezone.utc).isoformat()}
        if existing:
            return self.db.table("conversation_summaries").update(payload).eq("summary_id", existing[0]["summary_id"]).eq("user_id", user_id).execute().data[0]
        return self.db.table("conversation_summaries").insert({"summary_id": str(uuid4()), "user_id": user_id, "conversation_id": conversation_id, **payload}).execute().data[0]
