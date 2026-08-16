"""User-visible scheduling state; workers run separately from web requests."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from db.postgres import get_db
from services.auth_service import get_current_user
from services.jobs import JobService

router = APIRouter()


class PriceScheduleRequest(BaseModel):
    interval_seconds: int = Field(default=3600, ge=900, le=604800)
    enabled: bool = True


@router.get("")
def list_jobs(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return JobService(db).list_for_user(current_user["user_id"])


@router.put("/price-sync")
def configure_price_sync(
    body: PriceScheduleRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    row = JobService(db).ensure_schedule(
        "price_sync", current_user["user_id"], body.interval_seconds,
        {"respect_market_hours": True, "timezone": "Asia/Kolkata", "market_holidays": []},
    )
    if not body.enabled:
        row = db.table("job_schedules").update({"enabled": False}).eq(
            "job_schedule_id", row["job_schedule_id"]
        ).eq("user_id", current_user["user_id"]).execute().data[0]
    return row
