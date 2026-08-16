from services.qdrant_rag_service import PublicKnowledgeService


if __name__ == "__main__":
    print(PublicKnowledgeService().ingest_manifest())
