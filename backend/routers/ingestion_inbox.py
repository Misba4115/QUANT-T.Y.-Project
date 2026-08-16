"""Forwarding inbox setup and narrow provider webhook."""
from __future__ import annotations

import hmac
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field

from core.config import get_settings
from db.postgres import get_db
from services.auth_service import get_current_user
from services.inbox_ingestion import AttachmentRejected, InboxIngestionService

router = APIRouter()


class InboxSetupRequest(BaseModel):
    allowed_senders: list[EmailStr] = Field(default_factory=list, max_length=20)


@router.post("/setup")
def setup_inbox(
    body: InboxSetupRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    senders = [str(item) for item in body.allowed_senders] or [current_user["email"]]
    return InboxIngestionService(db).create_or_rotate_inbox(current_user["user_id"], senders)


@router.delete("/setup", status_code=204)
def revoke_inbox(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    InboxIngestionService(db).revoke(current_user["user_id"])


@router.post("/receive/{address_token}")
async def receive_statement(
    address_token: str,
    external_message_id: str = Form(min_length=1, max_length=240),
    sender: EmailStr = Form(),
    attachment: UploadFile = File(),
    webhook_secret: str | None = Header(default=None, alias="X-QUANT-Inbox-Secret"),
    db: Any = Depends(get_db),
):
    expected = get_settings().inbox_webhook_secret
    if not expected or not webhook_secret or not hmac.compare_digest(expected, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid ingestion webhook credential")
    content = await attachment.read(get_settings().max_upload_bytes + 1)
    if len(content) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=413, detail="Attachment exceeds configured size limit")
    try:
        return await InboxIngestionService(db).receive(
            address_token=address_token,
            external_message_id=external_message_id,
            sender=str(sender),
            filename=attachment.filename or "attachment",
            content_type=attachment.content_type or "application/octet-stream",
            content=content,
        )
    except AttachmentRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
