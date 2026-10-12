"""Groq chat-completions client (OpenAI-compatible API).

Groq is used here purely as a configured LLM_PROVIDER value -- nothing in
app/services/extraction.py is Groq-specific. Swapping to another
OpenAI-compatible provider only requires a new class implementing
LLMProvider and a branch in get_provider().
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.llm.base import LLMProvider, LLMProviderError


class GroqProvider(LLMProvider):
    name = "groq"

    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> str:
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMProviderError("Groq API key is not configured.")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

        try:
            with httpx.Client(timeout=settings.llm_request_timeout_seconds) as client:
                resp = client.post(
                    f"{settings.groq_base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.TimeoutException as exc:
            raise LLMProviderError(f"Groq request timed out after {settings.llm_request_timeout_seconds}s") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Groq request failed: {exc.__class__.__name__}") from exc

        if resp.status_code >= 400:
            raise LLMProviderError(f"Groq returned HTTP {resp.status_code}")

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError("Groq response had an unexpected shape") from exc
