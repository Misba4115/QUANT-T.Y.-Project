"""Owned conversation persistence around the LangGraph orchestrator."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from agents.chat_orchestrator import ChatOrchestrator
from db.postgres import get_db
from repositories.base import SupabaseRepository
from schemas.schemas import ChatRequest, ChatResponse
from services.conversation_memory import ConversationMemoryService
from services.auth_service import get_current_user

router = APIRouter()


def get_chat_orchestrator(db: Any = Depends(get_db)) -> ChatOrchestrator:
    return ChatOrchestrator(db)


def _owned_conversation(db: Any, conversation_id: str, user_id: str) -> dict | None:
    return SupabaseRepository(db).get_for_user("chat_conversations", conversation_id, user_id)


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    user_id = current_user["user_id"]
    conversation_id = body.conversation_id or str(uuid4())
    history: list[dict[str, str]] = []
    history_rows: list[dict[str, Any]] = []

    # 1. Manage conversation and fetch history safely
    if body.conversation_id:
        conversation = _owned_conversation(db, body.conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = body.conversation_id
    else:
        try:
            conv_insert = db.table("chat_conversations").insert(
                {"user_id": user_id, "conversation_title": body.message[:80]}
            ).execute()
            if conv_insert.data:
                conversation_id = conv_insert.data[0]["conversation_id"]
        except Exception as exc:
            import logging
            logging.warning("Could not persist new chat conversation: %s", exc)

    try:
        history_rows = (
            db.table("chat_messages").select("*").eq("conversation_id", conversation_id)
            .order("created_at", desc=True).limit(8).execute().data or []
        )
        history = [{"role": row["role"], "content": row["content"]} for row in reversed(history_rows)]
    except Exception as exc:
        import logging
        logging.warning("Chat conversation/history fetch degraded: %s", exc)

    # 2. Store user message safely
    user_insert_data = None
    try:
        user_insert = db.table("chat_messages").insert(
            {"conversation_id": conversation_id, "role": "user", "content": body.message}
        ).execute()
        if user_insert.data:
            user_insert_data = user_insert.data[0]
    except Exception as exc:
        import logging
        logging.warning("Could not persist user chat message: %s", exc)

    # 3. Run multi-agent orchestrator
    try:
        result = orchestrator.run(
            user_id,
            body.message,
            conversation_id,
            history=history,
            request_id=getattr(request.state, "request_id", None),
        )
    except Exception as exc:
        import logging
        logging.exception("Chat orchestrator error: %s", exc)
        result = {
            "reply": "I encountered an issue processing that query. You can ask me specific questions about your portfolio, net worth, tax 80C headroom, or financial goals!",
            "intent": "general",
            "agent": "manager",
            "citations": [],
            "warnings": [f"Orchestration degraded: {type(exc).__name__}"],
            "data_as_of": datetime.now(timezone.utc).isoformat(),
            "routing_confidence": 0.5,
            "selected_agents": [],
            "analysis_sections": [],
            "evidence_summary": {},
            "limitations": [],
            "degraded_dependencies": [],
        }

    # 4. Store assistant response and update conversation timestamp safely
    try:
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
        assistant_insert_data = assistant_insert.data[0] if assistant_insert.data else None

        db.table("chat_conversations").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("conversation_id", conversation_id).eq("user_id", user_id).execute()

        if user_insert_data and assistant_insert_data:
            ConversationMemoryService(db).update(
                user_id, conversation_id,
                [*history_rows, user_insert_data, assistant_insert_data],
            )
    except Exception as exc:
        import logging
        logging.warning("Could not persist assistant chat response: %s", exc)
        result.setdefault("warnings", []).append("Conversation persistence degraded")

    return ChatResponse(
        reply=result["reply"], conversation_id=conversation_id, intent=result["intent"],
        agent=result["agent"], citations=result["citations"], data_as_of=result["data_as_of"],
        warnings=result["warnings"],
        routing_confidence=result.get("routing_confidence"), consulted_agents=result.get("selected_agents", []),
        analysis_sections=result.get("analysis_sections", []), evidence_summary=result.get("evidence_summary", {}),
        limitations=result.get("limitations", []), degraded_dependencies=result.get("degraded_dependencies", []),
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
