"""
Chat Orchestrator — LangGraph RAG Pipeline
"""
# from langgraph.graph import StateGraph
# from langchain_openai import ChatOpenAI
# from sentence_transformers import SentenceTransformer
# from db.vector_db import get_qdrant_client


def run_chat_orchestrator(user_id: str, user_message: str, conversation_id: str, db) -> str:
    """
    LangGraph RAG pipeline for the chatbot.

    Node sequence in the StateGraph:
      embed_query → search_qdrant → fetch_user_context → generate_response → store_message

    Node details:
      1. embed_query:
           - Use SentenceTransformer (MiniLM) to embed user_message → vector
      2. search_qdrant:
           - Query 'financial_docs' collection (HNSW, cosine, top_k=5)
           - Returns relevant tax/SEBI/finance text chunks
      3. fetch_user_context:
           - Pull user holdings, goals, risk_profile from PostgreSQL
           - Pull last N messages from chat_messages for conversation history
      4. generate_response:
           - Build system prompt with retrieved docs + user context
           - Call the shared LLM service (Gemini by default; falls back to OpenAI)
             using environment variables GEMINI_API_KEY, GEMINI_MODEL, and
             LLM_PROVIDER.
           - Get assistant response text
      5. store_message:
           - INSERT user message into chat_messages
           - INSERT assistant message into chat_messages
           - Embed both and upsert into 'chat_messages_vec' Qdrant collection

    Returns:
        str: assistant reply text

    TODO: implement as LangGraph StateGraph
    """
    raise NotImplementedError("Chat orchestrator not implemented yet")
