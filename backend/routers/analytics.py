"""Educational technical analytics and explicitly experimental research."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from db.postgres import get_db
from services.analytics import AnalyticsService, synthetic_regimes
from services.auth_service import get_current_user

router = APIRouter()


class PriceSeriesRequest(BaseModel):
    instrument: str = Field(min_length=1, max_length=80)
    dates: list[str] = Field(min_length=35, max_length=5000)
    adjusted_closes: list[float] = Field(min_length=35, max_length=5000)
    source: str = Field(min_length=1, max_length=160)

    @model_validator(mode="after")
    def aligned(self):
        if len(self.dates) != len(self.adjusted_closes):
            raise ValueError("dates and adjusted_closes must have equal length")
        return self


class ForecastRequest(PriceSeriesRequest):
    window: int = Field(default=20, ge=10, le=120)


class SyntheticRequest(BaseModel):
    seed: int = 42
    days: int = Field(default=252, ge=30, le=5000)


@router.post("/indicators")
def indicators(
    body: PriceSeriesRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return AnalyticsService(db).indicators(
            current_user["user_id"], body.instrument, body.dates, body.adjusted_closes, body.source
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/forecast")
def forecast(
    body: ForecastRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return AnalyticsService(db).forecast(
            current_user["user_id"], body.instrument, body.dates, body.adjusted_closes, body.source, body.window
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/synthetic-sandbox")
def synthetic(body: SyntheticRequest, current_user: dict[str, Any] = Depends(get_current_user)):
    del current_user
    return synthetic_regimes(body.seed, body.days)
