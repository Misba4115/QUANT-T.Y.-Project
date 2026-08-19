"""Bounded fetch, hash, diff, review, publish, and rollback lifecycle."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from difflib import unified_diff
from typing import Callable
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from services.knowledge.registry import validate_official_url


MAX_DOCUMENT_BYTES = 15 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"text/html", "text/plain", "application/pdf"}


class KnowledgeLifecycle:
    def __init__(self, db, fetch: Callable[[str], tuple[bytes, str, str]] | None = None, indexer=None):
        self.db = db
        self.fetch = fetch or self._fetch
        self.indexer = indexer

    @staticmethod
    def _fetch(url: str) -> tuple[bytes, str, str]:
        validate_official_url(url)
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "QUANT-Knowledge/1.0"})
            response.raise_for_status()
        validate_official_url(str(response.url))
        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
        return response.content, content_type, str(response.url)

    def stage(self, source_id: str, document_url: str, *, title: str) -> dict:
        validate_official_url(document_url)
        content, content_type, final_url = self.fetch(document_url)
        validate_official_url(final_url)
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported authoritative document content type")
        if not content or len(content) > MAX_DOCUMENT_BYTES:
            raise ValueError("Authoritative document is empty or exceeds the size limit")
        digest = hashlib.sha256(content).hexdigest()
        prior = self.db.table("knowledge_document_versions").select("*").eq("source_id", source_id).eq("content_hash", digest).limit(1).execute().data or []
        if prior:
            return {**prior[0], "idempotent": True}
        previous = self.db.table("knowledge_document_versions").select("*").eq("source_id", source_id).order("retrieved_at", desc=True).limit(1).execute().data or []
        extracted = self._extract(content, content_type)
        if not extracted.strip():
            status, reason = "quarantined", "empty_extraction"
        else:
            status, reason = "staged", None
        version_id = str(uuid4())
        diff = ""
        if previous:
            diff = "\n".join(unified_diff(str(previous[0].get("extracted_text") or "").splitlines(), extracted.splitlines(), lineterm=""))[:100_000]
        row = self.db.table("knowledge_document_versions").insert({
            "knowledge_version_id": version_id, "source_id": source_id, "document_url": final_url,
            "title": title, "content_hash": digest, "content_type": content_type, "content_bytes": len(content),
            "extracted_text": extracted[:1_000_000], "diff_text": diff, "status": status,
            "quarantine_reason": reason, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "parser_version": "knowledge-extractor-v1",
        }).execute().data[0]
        if status == "staged":
            self.db.table("knowledge_reviews").insert({
                "knowledge_review_id": str(uuid4()), "knowledge_version_id": version_id,
                "status": "pending", "material_change": bool(previous and diff),
            }).execute()
        return {**row, "idempotent": False}

    def publish(self, version_id: str, reviewer_id: str) -> dict:
        versions = self.db.table("knowledge_document_versions").select("*").eq("knowledge_version_id", version_id).limit(1).execute().data or []
        reviews = self.db.table("knowledge_reviews").select("*").eq("knowledge_version_id", version_id).limit(1).execute().data or []
        if not versions or not reviews or reviews[0].get("status") != "approved":
            raise ValueError("An approved review is required before publication")
        version = versions[0]
        if self.indexer is not None:
            self.indexer.stage(version)
            self.indexer.promote(version_id)
        self.db.table("knowledge_document_versions").update({"status": "active", "published_at": datetime.now(timezone.utc).isoformat(), "published_by": reviewer_id}).eq("knowledge_version_id", version_id).execute()
        return {"status": "active", "knowledge_version_id": version_id}

    def rollback(self, version_id: str) -> dict:
        if self.indexer is not None:
            self.indexer.rollback(version_id)
        return {"status": "active", "knowledge_version_id": version_id, "rolled_back": True}

    @staticmethod
    def _extract(content: bytes, content_type: str) -> str:
        if content_type == "application/pdf":
            from io import BytesIO
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        text = content.decode("utf-8", errors="replace")
        if content_type == "text/html":
            import re
            text = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(text.split())
