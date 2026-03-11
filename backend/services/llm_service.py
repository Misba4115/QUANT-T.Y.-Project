"""
Light abstraction over LLM providers (Gemini / OpenAI fallback).
"""
import os
from typing import List, Dict

_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    """Return assistant text for a list of messages.

    Messages should be a list of dicts with `role` and `content` keys.  This
    wrapper insulates the rest of the code from the underlying provider.

    By default we use Google Gemini via the **AI Studio** API (free key).
    Set ``LLM_PROVIDER=openai`` to fall back to OpenAI using ``OPENAI_API_KEY``;
    this is mainly useful for local development when a Gemini key isn't
    available.
    """

    if _PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not api_key:
            print("Gemini provider selected but GEMINI_API_KEY is missing")
            return "Sorry, the AI service is not configured."

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            # assemble conversation as a simple prompt
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
            response = model.generate_content(prompt)
            # response may have a .text attribute or nested structure
            if hasattr(response, "text"):
                return response.text
            # fallback for object responses
            return str(response)
        except Exception as e:  # pragma: no cover - network/external error
            print(f"Gemini Error: {e}")
            return "Sorry, I'm unable to reach the AI service right now."

    # fallback to OpenAI
    try:
        import openai

        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:  # pragma: no cover
        print(f"OpenAI error: {e}")
        return "Sorry, I'm unable to reach the AI service right now."
