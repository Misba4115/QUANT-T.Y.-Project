"""Notification preferences, inbox state, and authenticated SSE delivery."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from db.postgres import get_db
from services.auth_service import get_current_user
from services.notifications import NotificationService

router = APIRouter()


class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    minimum_severity: Literal["info", "warning", "critical"] | None = None
    quiet_hours_start: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")
    quiet_hours_end: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    weekly_summary: bool | None = None


class NotificationAction(BaseModel):
    action: Literal["read", "acknowledge", "archive"]


@router.get("")
def list_notifications(
    include_archived: bool = False,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return NotificationService(db).list(current_user["user_id"], include_archived=include_archived)


@router.get("/preferences")
def get_preferences(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return NotificationService(db).preferences(current_user["user_id"])


@router.put("/preferences")
def update_preferences(
    body: NotificationPreferencesUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    return NotificationService(db).update_preferences(
        current_user["user_id"], body.model_dump(exclude_none=True)
    )


@router.patch("/{notification_id}")
def update_notification(
    notification_id: str,
    body: NotificationAction,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    try:
        return NotificationService(db).mark(notification_id, current_user["user_id"], body.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stream")
async def stream_notifications(
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    user_id = current_user["user_id"]

    async def events():
        cursor = last_event_id
        while not await request.is_disconnected():
            rows = list(reversed(NotificationService(db).list(user_id, limit=100)))
            if cursor:
                ids = [row["notification_id"] for row in rows]
                rows = rows[ids.index(cursor) + 1 :] if cursor in ids else []
            for row in rows:
                cursor = row["notification_id"]
                public = {key: value for key, value in row.items() if key not in {"user_id", "evidence"}}
                yield f"id: {cursor}\nevent: notification\ndata: {json.dumps(public, default=str)}\n\n"
            yield ": heartbeat\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
