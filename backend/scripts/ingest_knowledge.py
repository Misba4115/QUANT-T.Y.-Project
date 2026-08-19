import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.qdrant_rag_service import PublicKnowledgeService


if __name__ == "__main__":
    print(PublicKnowledgeService().ingest_manifest())
