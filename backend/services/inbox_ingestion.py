"""Secure forwarding-inbox metadata, attachment scanning, storage, and preview."""
from __future__ import annotations

import hashlib
import io
import secrets
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from core.config import get_settings
from repositories.base import SupabaseRepository
from services.import_service import preview_import
from services.secrets import SecretBox


class AttachmentRejected(ValueError):
    pass


class EncryptedBlobStore(Protocol):
    def put(self, key: str, content: bytes) -> None: ...
    def delete(self, key: str) -> None: ...


class SupabaseEncryptedBlobStore:
    bucket = "quant-secure-ingestion"

    def __init__(self, db: Any):
        self.db = db

    def put(self, key: str, content: bytes) -> None:
        try:
            self.db.storage.from_(self.bucket).upload(
                key, content, {"content-type": "application/octet-stream", "upsert": "false"}
            )
        except Exception as exc:
            raise RuntimeError(
                "Encrypted ingestion storage is unavailable; configure the private quant-secure-ingestion bucket"
            ) from exc

    def delete(self, key: str) -> None:
        self.db.storage.from_(self.bucket).remove([key])


class MemoryBlobStore:
    def __init__(self):
        self.values: dict[str, bytes] = {}

    def put(self, key: str, content: bytes) -> None:
        self.values[key] = content

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


class AttachmentScanner:
    supported = {".csv", ".xlsx", ".pdf"}
    executable_magic = (b"MZ", b"\x7fELF", b"#!")

    def scan(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.supported:
            raise AttachmentRejected("Unsupported attachment type")
        if not content:
            raise AttachmentRejected("Attachment is empty")
        if any(content.startswith(magic) for magic in self.executable_magic):
            raise AttachmentRejected("Executable content is not accepted")
        if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
            raise AttachmentRejected("Attachment failed the malware signature scan")
        if suffix == ".pdf" and not content.startswith(b"%PDF"):
            raise AttachmentRejected("PDF signature is invalid")
        if suffix == ".csv" and b"\x00" in content[:4096]:
            raise AttachmentRejected("Delimited file contains binary content")
        if suffix == ".xlsx":
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    infos = archive.infolist()
                    if len(infos) > 500 or sum(info.file_size for info in infos) > 50 * 1024 * 1024:
                        raise AttachmentRejected("Spreadsheet archive exceeds safe expansion limits")
                    if any(info.flag_bits & 0x1 for info in infos):
                        raise AttachmentRejected("Encrypted spreadsheets are not supported")
                    if any(name.lower().endswith((".exe", ".dll", ".js", ".vbs")) for name in archive.namelist()):
                        raise AttachmentRejected("Spreadsheet contains an unsafe embedded file")
            except zipfile.BadZipFile as exc:
                raise AttachmentRejected("Spreadsheet container is invalid") from exc
        return hashlib.sha256(content).hexdigest()


def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


class InboxIngestionService:
    def __init__(
        self,
        db: Any,
        *,
        blob_store: EncryptedBlobStore | None = None,
        scanner: AttachmentScanner | None = None,
        secret_box: SecretBox | None = None,
    ):
        self.db = db
        self.repo = SupabaseRepository(db)
        self.blob_store = blob_store or SupabaseEncryptedBlobStore(db)
        self.scanner = scanner or AttachmentScanner()
        self.secret_box = secret_box or SecretBox()

    def create_or_rotate_inbox(self, user_id: str, allowed_senders: list[str]) -> dict[str, Any]:
        token = secrets.token_urlsafe(24)
        payload = {
            "address_token_hash": _hash(token),
            "status": "active",
            "allowed_senders": [_hash(sender) for sender in sorted(set(allowed_senders))],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        rows = self.repo.list_for_user("ingestion_inboxes", user_id, limit=1)
        if rows:
            stored = self.db.table("ingestion_inboxes").update(payload).eq(
                "ingestion_inbox_id", rows[0]["ingestion_inbox_id"]
            ).eq("user_id", user_id).execute().data[0]
        else:
            stored = self.db.table("ingestion_inboxes").insert(
                {**payload, "ingestion_inbox_id": str(uuid4()), "user_id": user_id}
            ).execute().data[0]
        return {
            "ingestion_inbox_id": stored["ingestion_inbox_id"],
            "forwarding_address": f"statements+{token}@{get_settings().inbox_domain}",
            "allowed_sender_count": len(payload["allowed_senders"]),
            "warning": "The forwarding address is shown once. Rotate it if exposed.",
        }

    def revoke(self, user_id: str) -> None:
        self.db.table("ingestion_inboxes").update(
            {"status": "revoked", "updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_id", user_id).execute()

    async def receive(
        self,
        *,
        address_token: str,
        external_message_id: str,
        sender: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> dict[str, Any]:
        rows = self.repo.find(
            "ingestion_inboxes", [("address_token_hash", _hash(address_token)), ("status", "active")], limit=1
        )
        if not rows:
            raise AttachmentRejected("Inbox address is invalid or revoked")
        inbox = rows[0]
        sender_hash = _hash(sender)
        if inbox.get("allowed_senders") and sender_hash not in inbox["allowed_senders"]:
            raise AttachmentRejected("Sender is not authorized for this inbox")
        attachment_hash = self.scanner.scan(filename, content)
        existing = self.repo.find(
            "ingestion_messages",
            [
                ("ingestion_inbox_id", inbox["ingestion_inbox_id"]),
                ("external_message_id", external_message_id),
                ("attachment_hash", attachment_hash),
            ],
            limit=1,
        )
        if existing:
            return {**existing[0], "duplicate": True}
        message_id = str(uuid4())
        storage_key = f"{inbox['user_id']}/{message_id}/{Path(filename).name}.encrypted"
        self.blob_store.put(storage_key, self.secret_box.encrypt_bytes(content))
        row = self.db.table("ingestion_messages").insert(
            {
                "ingestion_message_id": message_id,
                "user_id": inbox["user_id"],
                "ingestion_inbox_id": inbox["ingestion_inbox_id"],
                "external_message_id": external_message_id[:240],
                "sender_hash": sender_hash,
                "attachment_hash": attachment_hash,
                "filename": Path(filename).name[:240],
                "content_type": content_type[:120],
                "byte_size": len(content),
                "storage_key": storage_key,
                "status": "received",
                "purge_after": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            }
        ).execute().data[0]
        try:
            upload = UploadFile(filename=Path(filename).name, file=io.BytesIO(content))
            preview = await preview_import(upload, inbox["user_id"], self.db)
            row = self.db.table("ingestion_messages").update(
                {"status": "review_ready", "import_batch_id": preview["import_batch_id"]}
            ).eq("ingestion_message_id", message_id).eq("user_id", inbox["user_id"]).execute().data[0]
            from services.notifications import NotificationService

            NotificationService(self.db).create(
                user_id=inbox["user_id"],
                event_key=f"statement-review:{message_id}",
                category="import",
                severity="info",
                title="Statement ready for review",
                body=f"{Path(filename).name} was parsed. Review the preview before committing any records.",
                evidence={"import_batch_id": preview["import_batch_id"]},
                deep_link=f"/csv-files?batch={preview['import_batch_id']}",
            )
            return {**row, "duplicate": False}
        except Exception as exc:
            self.db.table("ingestion_messages").update(
                {"status": "failed", "rejection_reason": str(exc)[:500]}
            ).eq("ingestion_message_id", message_id).eq("user_id", inbox["user_id"]).execute()
            raise
