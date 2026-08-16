"""Owned conversation persistence around the LangGraph orchestrator."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from agents.chat_orchestrator import ChatOrchestrator
from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import ChatRequest, ChatResponse
from services.auth_service import get_current_user

router = APIRouter()


def get_chat_orchestrator(db: Any = Depends(get_db)) -> ChatOrchestrator:
    return ChatOrchestrator(db)


def _owned_conversation(db: Any, conversation_id: str, user_id: str) -> dict | None:
    return SupabaseRepository(db).get_for_user("chat_conversations", conversation_id, user_id)


@router.post("/", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    user_id = current_user["user_id"]
    if body.conversation_id:
        conversation = _owned_conversation(db, body.conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = body.conversation_id
    else:
        result = db.table("chat_conversations").insert(
            {"user_id": user_id, "conversation_title": body.message[:80]}
        ).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Conversation could not be created")
        conversation_id = result.data[0]["conversation_id"]

    history_rows = (
        db.table("chat_messages").select("*").eq("conversation_id", conversation_id)
        .order("created_at", desc=True).limit(8).execute().data or []
    )
    history = [{"role": row["role"], "content": row["content"]} for row in reversed(history_rows)]
    user_insert = db.table("chat_messages").insert(
        {"conversation_id": conversation_id, "role": "user", "content": body.message}
    ).execute()
    if not user_insert.data:
        raise HTTPException(status_code=500, detail="Message could not be stored")

    result = orchestrator.run(
        user_id,
        body.message,
        conversation_id,
        history=history,
        request_id=getattr(request.state, "request_id", None),
    )
    assistant_insert = db.table("chat_messages").insert(
        {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": result["reply"],
            "metadata": {
                "intent": result["intent"], "agent": result["agent"],
                "citations": result["citations"], "warnings": result["warnings"],
            },
        }
    ).execute()
    if not assistant_insert.data:
        raise HTTPException(status_code=500, detail="Assistant response could not be stored")
    db.table("chat_conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("conversation_id", conversation_id).eq("user_id", user_id).execute()
    return ChatResponse(
        reply=result["reply"], conversation_id=conversation_id, intent=result["intent"],
        agent=result["agent"], citations=result["citations"], data_as_of=result["data_as_of"],
        warnings=result["warnings"],
    )


@router.get("/conversations")
def list_conversations(current_user: dict[str, Any] = Depends(get_current_user), db: Any = Depends(get_db)):
    return SupabaseRepository(db).list_for_user(
        "chat_conversations", current_user["user_id"], order_by="updated_at", descending=True
    )


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    if not _owned_conversation(db, conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute().data or []
