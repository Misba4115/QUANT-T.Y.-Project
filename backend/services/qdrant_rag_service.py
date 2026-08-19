"""Curated public Indian-finance knowledge ingestion and retrieval."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from core.config import get_settings
from db.vector_db import get_qdrant_client


def probe_public_knowledge(client: Any | None = None) -> dict[str, Any]:
    """Probe Qdrant without loading the embedding model."""
    settings = get_settings()
    client = client or get_qdrant_client()
    name = settings.qdrant_collection
    try:
        if not client.collection_exists(name):
            return {"status": "insufficient_data", "reason_code": "collection_missing", "reachable": True, "collection": name, "document_count": 0, "chunk_count": 0, "retryable": True}
        info = client.get_collection(name)
        vectors = info.config.params.vectors
        size = int(vectors.size) if hasattr(vectors, "size") else None
        count = int(getattr(info, "points_count", len(getattr(client, "points", {}))) or 0)
        if size != settings.qdrant_vector_size:
            return {"status": "failed", "reason_code": "vector_dimension_mismatch", "reachable": True, "collection": name, "vector_size": size, "chunk_count": count, "retryable": False}
        records, _offset = client.scroll(collection_name=name, limit=1000, offset=None, with_payload=True, with_vectors=False)
        payloads = [dict(item.payload or {}) for item in records]
        documents = {item.get("source_url") or item.get("source_file") for item in payloads if item.get("source_url") or item.get("source_file")}
        corpus_parts = sorted({str(item.get("content_hash")) for item in payloads if item.get("content_hash")})
        corpus_version = hashlib.sha256("|".join(corpus_parts).encode()).hexdigest() if corpus_parts else None
        return {"status": "available" if count else "insufficient_data", "reason_code": "ready" if count else "collection_empty", "reachable": True, "collection": name, "vector_size": size, "chunk_count": count, "document_count": len(documents), "active_corpus_version": corpus_version, "retryable": not bool(count)}
    except Exception as exc:
        return {"status": "provider_unavailable", "reason_code": "qdrant_probe_failed", "reachable": False, "collection": name, "error_class": type(exc).__name__, "retryable": True}


class PublicEmbedder(Protocol):
    model: str
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    model = "sentence-transformers/all-MiniLM-L6-v2"
    dimension = 384

    def __init__(self):
        self.encoder = _load_sentence_transformer(self.model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.encoder.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


@lru_cache(maxsize=1)
def _load_sentence_transformer(model: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-ml.txt to ingest or query the public Qdrant knowledge base") from exc
    return SentenceTransformer(model)


def _chunks(text: str, maximum_words: int = 180, overlap: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, maximum_words - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + maximum_words])
        if chunk:
            chunks.append(chunk)
        if start + maximum_words >= len(words):
            break
    return chunks


class PublicKnowledgeService:
    def __init__(self, client: Any | None = None, embedder: PublicEmbedder | None = None):
        self.settings = get_settings()
        self.client = client or get_qdrant_client()
        self.embedder = embedder or SentenceTransformerEmbedder()
        if self.embedder.dimension != self.settings.qdrant_vector_size:
            raise RuntimeError("Qdrant vector size does not match the configured public embedder")

    def ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams

        name = self.settings.qdrant_collection
        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=self.embedder.dimension, distance=Distance.COSINE),
            )
            return
        info = self.client.get_collection(name)
        vectors = info.config.params.vectors
        size = vectors.size if hasattr(vectors, "size") else None
        if size is not None and int(size) != self.embedder.dimension:
            raise RuntimeError(f"Qdrant collection dimension is {size}; expected {self.embedder.dimension}")

    def readiness(self) -> dict[str, Any]:
        """Actively verify reachability, collection shape, and population."""
        return probe_public_knowledge(self.client)

    def ingest_manifest(self, manifest_path: Path | None = None) -> dict[str, int]:
        from qdrant_client.models import PointIdsList, PointStruct

        root = Path(__file__).resolve().parents[1] / "knowledge_docs"
        manifest_path = manifest_path or root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.ensure_collection()
        points = []
        active_ids: set[str] = set()
        for document in manifest["documents"]:
            content = (root / document["file"]).read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunks = _chunks(content)
            vectors = self.embedder.embed(chunks)
            if len(vectors) != len(chunks) or any(len(vector) != self.embedder.dimension for vector in vectors):
                raise RuntimeError("Public embedder returned an invalid vector batch")
            for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
                point_id = str(uuid5(NAMESPACE_URL, f"{document['source_url']}:{content_hash}:{index}:{self.embedder.model}"))
                active_ids.add(point_id)
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "title": document["title"],
                            "authority": document["authority"],
                            "source_url": document["source_url"],
                            "effective_date": document.get("effective_date"),
                            "retrieved_date": document["retrieved_date"],
                            "source_file": document["file"],
                            "content_hash": content_hash,
                            "chunk_index": index,
                            "parser_version": manifest["parser_version"],
                            "embedding_model": self.embedder.model,
                            "content": chunk,
                        },
                    )
                )
        if points:
            self.client.upsert(collection_name=self.settings.qdrant_collection, points=points, wait=True)
        managed_files = {document["file"] for document in manifest["documents"]}
        stale_ids: list[Any] = []
        offset = None
        while True:
            records, offset = self.client.scroll(
                collection_name=self.settings.qdrant_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                if (record.payload or {}).get("source_file") in managed_files and str(record.id) not in active_ids:
                    stale_ids.append(record.id)
            if offset is None:
                break
        if stale_ids:
            self.client.delete(
                collection_name=self.settings.qdrant_collection,
                points_selector=PointIdsList(points=stale_ids),
                wait=True,
            )
        return {"documents": len(manifest["documents"]), "chunks": len(points), "deleted_stale_chunks": len(stale_ids)}

    def search(self, query: str, limit: int = 5, threshold: float = 0.45) -> list[dict[str, Any]]:
        self.ensure_collection()
        vector = self.embedder.embed([query])[0]
        response = self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=vector,
            limit=max(1, min(limit, 10)),
            score_threshold=threshold,
            with_payload=True,
        )
        points = getattr(response, "points", response)
        references = []
        for point in points:
            payload = dict(point.payload or {})
            references.append(
                {
                    "citation_id": f"public:{point.id}",
                    "title": payload.get("title", "Untitled source"),
                    "source_type": "public_knowledge",
                    "source_url": payload.get("source_url"),
                    "authority": payload.get("authority"),
                    "effective_date": payload.get("effective_date"),
                    "retrieved_date": payload.get("retrieved_date"),
                    "excerpt": payload.get("content"),
                    "locator": f"chunk {int(payload.get('chunk_index', 0)) + 1}",
                    "similarity": float(point.score),
                }
            )
        return references
