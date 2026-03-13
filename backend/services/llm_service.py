"""
Light abstraction over LLM providers (Gemini only).
"""
import os
from typing import List, Dict


def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    """Return assistant text for a list of messages.

    Messages should be a list of dicts with `role` and `content` keys.
    Uses Google Gemini via the **AI Studio** API (free key).
    """

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    if not api_key:
        print("GEMINI_API_KEY is missing")
        return "Sorry, the AI service is not configured."

    try:
        from google import genai  # NEW library

        client = genai.Client(api_key=api_key)
        
        # Assemble conversation as a simple prompt
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        return response.text
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Sorry, I'm unable to reach the AI service right now."