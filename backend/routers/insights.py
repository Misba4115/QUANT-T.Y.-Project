"""Insights & Trading tab — generate and retrieve endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from db.postgres import get_db
from services.auth_service import get_current_user
from services.insights_service import InsightsService
from pydantic import BaseModel, ConfigDict, Field
from services.insights.recommendation_algorithm import build_recommendations, create_custom_platform, valid_selection

router = APIRouter()

# In-memory cache: user_id → {result, generated_at}
# Keeps the tab fast on repeated opens. Cleared on generate.
_cache: dict[str, dict[str, Any]] = {}
STALE_HOURS = 4


class ComparisonSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: str = Field(min_length=1, max_length=80)
    option_id: str = Field(min_length=1, max_length=80)
    platform_id: str = Field(min_length=1, max_length=80)
    years: int = Field(default=5, ge=1, le=20)
    amount: float = Field(default=10000, ge=1, le=100000000, allow_inf_nan=False)


class CustomPlatform(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)


@router.get("/discovery")
def discovery(db: Any = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        return build_recommendations(db, current_user["user_id"])
    except Exception as exc:
        raise HTTPException(503, "Portfolio discovery is unavailable. Please retry.") from exc


@router.post("/platforms", status_code=201)
def add_platform(body: CustomPlatform, db: Any = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        platform_id = create_custom_platform(db, current_user["user_id"], body.category_id, body.name)
        return {"id": platform_id}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, "Could not save your provider. Check database migration 010 and retry.") from exc


@router.get("/comparisons")
def comparisons(db: Any = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        return db.table("investment_comparisons").select("category_id,option_id,platform_id,years,amount").eq(
            "user_id", current_user["user_id"]).order("created_at").execute().data or []
    except Exception as exc:
        raise HTTPException(503, "Saved comparisons are unavailable. Check database migration 009 and retry.") from exc


@router.put("/comparisons")
def save_comparison(body: ComparisonSelection, db: Any = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not valid_selection(body.category_id, body.option_id, body.platform_id, db, current_user["user_id"]):
        raise HTTPException(422, "Unknown investment or incompatible platform")
    try:
        db.table("investment_comparisons").upsert(
            {**body.model_dump(), "user_id": current_user["user_id"]},
            on_conflict="user_id,category_id,option_id,platform_id").execute()
        return body.model_dump()
    except Exception as exc:
        raise HTTPException(503, "Could not save comparison. Please retry.") from exc


@router.delete("/comparisons/{category_id}/{option_id}/{platform_id}", status_code=204)
def remove_comparison(category_id: str, option_id: str, platform_id: str,
                      db: Any = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        db.table("investment_comparisons").delete().eq("user_id", current_user["user_id"]).eq(
            "category_id", category_id).eq("option_id", option_id).eq("platform_id", platform_id).execute()
    except Exception as exc:
        raise HTTPException(503, "Could not remove comparison. Please retry.") from exc


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
