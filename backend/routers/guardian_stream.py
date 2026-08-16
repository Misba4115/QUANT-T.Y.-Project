"""Real-time Guardian event and evidence endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db.postgres import get_db
from services.auth_service import get_current_user
from services.guardian_stream import GuardianStreamService

router = APIRouter()


class GuardianEventRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=160)
    asset_type: Literal["equity", "mutual_fund", "etf", "crypto", "bank"]
    event_type: str = Field(min_length=1, max_length=80)
    occurred_at: datetime
    payload: dict[str, Any]


class GuardianFeedbackRequest(BaseModel):
    verdict: Literal["expected", "incorrect", "investigate"]
    note: str | None = Field(default=None, max_length=500)


@router.post("/events", status_code=202)
def ingest_event(
    body: GuardianEventRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return GuardianStreamService(db).ingest(user_id=current_user["user_id"], **body.model_dump())


@router.get("/alerts")
def list_alerts(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return GuardianStreamService(db).alerts(current_user["user_id"])


@router.put("/alerts/{alert_id}/feedback")
def submit_feedback(
    alert_id: str,
    body: GuardianFeedbackRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return GuardianStreamService(db).feedback(
            current_user["user_id"], alert_id, body.verdict, body.note
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
