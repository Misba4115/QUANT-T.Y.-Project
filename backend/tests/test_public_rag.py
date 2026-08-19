from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from services.qdrant_rag_service import PublicKnowledgeService


class FakePublicEmbedder:
    model = "sentence-transformers/all-MiniLM-L6-v2"
    dimension = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text) % 13)] + [0.0] * 383 for text in texts]


class FakeQdrant:
    def __init__(self):
        self.exists = False
        self.points = {}

    def collection_exists(self, _name):
        return self.exists

    def create_collection(self, collection_name, vectors_config):
        self.exists = True
        self.size = vectors_config.size

    def get_collection(self, _name):
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(vectors=SimpleNamespace(size=self.size))))

    def upsert(self, collection_name, points, wait):
        for point in points:
            self.points[str(point.id)] = point

    def scroll(self, collection_name, limit, offset, with_payload, with_vectors):
        return list(self.points.values()), None

    def delete(self, collection_name, points_selector, wait):
        for point_id in points_selector.points:
            self.points.pop(str(point_id), None)

    def query_points(self, collection_name, query, limit, score_threshold, with_payload):
        selected = list(self.points.values())[:limit]
        return SimpleNamespace(
            points=[SimpleNamespace(id=point.id, payload=point.payload, score=0.88) for point in selected]
        )


def test_manifest_ingestion_is_idempotent_and_search_returns_traceable_citations():
    client = FakeQdrant()
    service = PublicKnowledgeService(client, FakePublicEmbedder())
    first = service.ingest_manifest()
    assert first["documents"] == 2
    assert first["chunks"] >= 2
    count = len(client.points)
    second = service.ingest_manifest()
    assert second["chunks"] == first["chunks"]
    assert len(client.points) == count

    results = service.search("What evidence is required for equity tax calculations?", limit=2)
    assert results
    assert all(item["citation_id"].startswith("public:") for item in results)
    assert all(item["source_url"].startswith("https://") for item in results)
    assert all(item["authority"] for item in results)
    assert all(item["excerpt"] for item in results)
    readiness = service.readiness()
    assert readiness["status"] == "available"
    assert readiness["chunk_count"] == len(client.points)
    assert readiness["document_count"] == 2
    assert readiness["active_corpus_version"]
