from typing import Any

from fastapi import APIRouter, Depends, Query

from services.auth_service import get_current_user
from services.qdrant_rag_service import PublicKnowledgeService

router = APIRouter()


@router.get("/public/search")
def public_search(
    q: str = Query(min_length=2, max_length=500),
    limit: int = Query(default=5, ge=1, le=10),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    results = PublicKnowledgeService().search(q, limit=limit)
    return {"results": results, "grounded": bool(results)}
