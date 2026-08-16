"""Lazy Qdrant configuration for the public knowledge store."""
from __future__ import annotations

from functools import lru_cache

from core.config import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client():
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=10)


def clear_qdrant_client() -> None:
    get_qdrant_client.cache_clear()
