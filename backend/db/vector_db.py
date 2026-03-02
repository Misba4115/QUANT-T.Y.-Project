"""
Qdrant Vector Database Client
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL   = os.getenv("QDRANT_URL", "http://localhost:6333")
VECTOR_SIZE  = 384   # MiniLM / all-MiniLM-L6-v2 output size

# Collections used in QUANT
COLLECTION_FINANCIAL_DOCS   = "financial_docs"
COLLECTION_CHAT_MESSAGES_VEC = "chat_messages_vec"


def get_qdrant_client() -> QdrantClient:
    """Return a connected Qdrant client."""
    return QdrantClient(url=QDRANT_URL)


def ensure_collections(client: QdrantClient):
    """
    Create Qdrant collections if they don't already exist.
    Call this once on application startup.
    """
    existing = {c.name for c in client.get_collections().collections}

    if COLLECTION_FINANCIAL_DOCS not in existing:
        client.create_collection(
            collection_name=COLLECTION_FINANCIAL_DOCS,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    if COLLECTION_CHAT_MESSAGES_VEC not in existing:
        client.create_collection(
            collection_name=COLLECTION_CHAT_MESSAGES_VEC,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
