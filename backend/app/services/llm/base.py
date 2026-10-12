"""Provider-agnostic interface for text-extraction LLM calls.

Any OpenAI-chat-completions-compatible provider can implement this without
touching the extraction orchestration logic in app/services/extraction.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Raised for network failures, timeouts, or non-2xx provider responses.
    Never includes the API key or raw headers in its message.
    """


class LLMProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Return the raw text content of the model's response. Callers are
        responsible for JSON-parsing and schema validation.
        """
        raise NotImplementedError
