"""Insights & Trading tab — generate and retrieve endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from db.postgres import get_db
from services.auth_service import get_current_user
from services.insights_service import InsightsService

router = APIRouter()

# In-memory cache: user_id → {result, generated_at}
# Keeps the tab fast on repeated opens. Cleared on generate.
_cache: dict[str, dict[str, Any]] = {}
STALE_HOURS = 4


def _is_stale(cached: dict[str, Any]) -> bool:
    try:
        generated = datetime.fromisoformat(cached["generated_at"])
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - generated).total_seconds() / 3600
        return age > STALE_HOURS
    except (KeyError, ValueError):
        return True


@router.post("/generate")
def generate_insights(
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Compute Layer A (trading signals) + Layer B (investment recommendations).
    Results are cached in memory per user; force-refresh with this endpoint.
    """
    user_id = current_user["user_id"]
    try:
        result = InsightsService(db).generate(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Insights generation failed: {type(exc).__name__}: {exc}",
        ) from exc

    _cache[user_id] = result
    return result


@router.get("/latest")
def latest_insights(
    db: Any = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Return cached insights for this user.
    If no cache exists or the cache is stale (>4h), triggers a fresh generate.
    """
    user_id = current_user["user_id"]
    cached = _cache.get(user_id)

    if cached is None or _is_stale(cached):
        # Trigger inline — session-triggered re-evaluation as per plan
        try:
            result = InsightsService(db).generate(user_id)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Insights generation failed: {type(exc).__name__}: {exc}",
            ) from exc
        _cache[user_id] = result
        return result

    return cached
