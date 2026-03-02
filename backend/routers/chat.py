"""
Chat Router — POST /chat
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db

router = APIRouter()


@router.post("/")
async def chat(db: AsyncSession = Depends(get_db)):
    """
    RAG-based chatbot endpoint.
    Steps:
      1. Embed user message (Sentence-BERT)
      2. Retrieve top-k relevant docs from Qdrant (financial_docs)
      3. Pull user's holdings + goals from PostgreSQL for context
      4. Call GPT-4o with context + user message
      5. Store message + embedding in chat_messages / chat_messages_vec
      6. Return assistant reply
    TODO: implement with chat_orchestrator agent
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all chat conversations for the user. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch message history for a conversation. TODO: implement"""
    raise HTTPException(status_code=501, detail="Not implemented yet")
