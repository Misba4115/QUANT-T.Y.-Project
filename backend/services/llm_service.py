"""Configured chat-model adapter. Failures are explicit to the orchestrator."""
from __future__ import annotations

import json
from typing import Any

from core.config import get_settings


def generate_chat_response(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini chat is not configured")
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = "\n\n".join(f"{message['role'].upper()}: {message['content']}" for message in messages)
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        text = str(response.text or "").strip()
    else:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI chat is not configured")
        from openai import OpenAI

        response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
            model="gpt-4.1-mini", messages=messages, temperature=0.2
        )
        text = str(response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("The chat provider returned an empty response")
    return text


def generate_structured_response(messages: list[dict[str, str]], json_schema: dict[str, Any]) -> dict[str, Any]:
    """Use provider-native JSON constraints instead of parsing free-form prose."""
    settings = get_settings()
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini chat is not configured")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = "\n\n".join(f"{message['role'].upper()}: {message['content']}" for message in messages)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_json_schema=json_schema,
            ),
        )
        text = str(response.text or "").strip()
    else:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI chat is not configured")
        from openai import OpenAI

        response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.1,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "quant_import_mapping", "strict": True, "schema": json_schema},
            },
        )
        text = str(response.choices[0].message.content or "").strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeError("The structured model response was not an object")
    return value
