"""Extraction orchestration: brief (+ optional image context) -> validated
RawExtraction, with bounded retries, JSON repair, model fallback, and a
documented safe-degradation path. This module is the only place that
decides *how* a value was obtained; it never crashes the request.
"""
from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.core.config import get_settings
from app.models.enums import ExtractionMethod
from app.models.extraction_raw import RawExtraction
from app.models.schemas import RecoveryEvent
from app.services.llm.base import LLMProviderError
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.offline_extractor import extract_offline

_ENUM_HINT = """
Respond with ONLY a JSON object (no markdown fences, no commentary) using exactly these keys.
Use null for anything not stated or not confidently inferable -- never invent a value.
{
  "product_type": "ring" | null,
  "design_category": "engagement_ring" | "wedding_band" | "eternity_band" | "cocktail_ring" | "solitaire" | "halo_ring" | "three_stone" | "cluster_ring" | null,
  "metal_type": "gold" | "platinum" | "silver" | "palladium" | null,
  "metal_purity": "10k" | "14k" | "18k" | "22k" | "24k" | "950_platinum" | "925_silver" | null,
  "metal_color": "yellow" | "white" | "rose" | "two_tone" | null,
  "setting_type": "prong" | "pave" | "bezel" | "halo" | "channel" | "tension" | "cluster" | null,
  "ring_size_us": number | null,
  "band_width_mm": number | null,
  "center_stone_type": "diamond" | "sapphire" | "ruby" | "emerald" | "moissanite" | "morganite" | "aquamarine" | "amethyst" | "topaz" | "pearl" | "other" | null,
  "center_stone_shape": "round" | "oval" | "princess" | "cushion" | "emerald_cut" | "pear" | "marquise" | "radiant" | "asscher" | "heart" | null,
  "center_stone_carat": number | null,
  "side_stone_type": same enum as center_stone_type | null,
  "side_stone_shape": same enum as center_stone_shape | null,
  "side_stone_count_total": integer | null,
  "side_stone_total_carat": number | null,
  "notes": string | null
}
""".strip()

SYSTEM_PROMPT = (
    "You are a structured-data extractor for a custom jewelry sales brief. "
    "Extract ONLY what is stated or very strongly implied by the text. "
    "Do not guess missing attributes. " + _ENUM_HINT
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_and_validate(raw_text: str) -> RawExtraction:
    cleaned = _strip_fences(raw_text)
    payload = json.loads(cleaned)  # may raise json.JSONDecodeError
    return RawExtraction.model_validate(payload)  # may raise ValidationError


class ExtractionResult:
    def __init__(
        self,
        raw: RawExtraction,
        method: ExtractionMethod,
        recovery_events: list[RecoveryEvent],
        provider: str | None,
        model_used: str | None,
    ):
        self.raw = raw
        self.method = method
        self.recovery_events = recovery_events
        self.provider = provider
        self.model_used = model_used


def _try_model(provider: GroqProvider, brief: str, model: str, recovery_events: list[RecoveryEvent], max_attempts: int) -> RawExtraction | None:
    user_prompt = f"Sales brief:\n\"\"\"\n{brief}\n\"\"\""
    last_error: str = ""
    for attempt in range(1, max_attempts + 1):
        prompt = user_prompt
        if attempt > 1 and last_error:
            prompt += (
                f"\n\nYour previous response was invalid ({last_error}). "
                "Return corrected JSON that strictly matches the schema."
            )
        try:
            raw_text = provider.generate_json(SYSTEM_PROMPT, prompt, model)
        except LLMProviderError as exc:
            last_error = str(exc)
            recovery_events.append(
                RecoveryEvent(stage="extraction", action="provider_call_failed",
                               detail=f"model={model} attempt={attempt}: {last_error}")
            )
            continue

        try:
            parsed = _parse_and_validate(raw_text)
            if attempt > 1:
                recovery_events.append(
                    RecoveryEvent(stage="extraction", action="json_repaired",
                                  detail=f"model={model} succeeded on retry attempt {attempt}")
                )
            return parsed
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = f"{exc.__class__.__name__}: {str(exc)[:200]}"
            recovery_events.append(
                RecoveryEvent(stage="extraction", action="invalid_model_output",
                              detail=f"model={model} attempt={attempt}: {last_error}")
            )
    return None


def extract_specification_raw(brief: str) -> ExtractionResult:
    settings = get_settings()
    recovery_events: list[RecoveryEvent] = []

    if not settings.live_mode_ready:
        if settings.is_live_mode and not recovery_events:
            recovery_events.append(
                RecoveryEvent(stage="extraction", action="live_mode_unconfigured",
                               detail="Live mode requested but no provider API key is configured; using offline fixture extraction.")
            )
        raw = extract_offline(brief)
        return ExtractionResult(raw, ExtractionMethod.OFFLINE_FIXTURE, recovery_events, None, None)

    provider = GroqProvider()

    primary = _try_model(provider, brief, settings.llm_primary_model, recovery_events, settings.llm_max_retries)
    if primary is not None:
        method = ExtractionMethod.LLM_LIVE if not recovery_events else ExtractionMethod.LLM_REPAIRED
        return ExtractionResult(primary, method, recovery_events, provider.name, settings.llm_primary_model)

    recovery_events.append(
        RecoveryEvent(stage="extraction", action="primary_model_exhausted",
                       detail=f"Primary model {settings.llm_primary_model} failed after {settings.llm_max_retries} attempt(s); trying fallback model.")
    )

    fallback = _try_model(provider, brief, settings.llm_fallback_model, recovery_events, 1)
    if fallback is not None:
        return ExtractionResult(
            fallback, ExtractionMethod.LLM_LIVE_FALLBACK_MODEL, recovery_events, provider.name, settings.llm_fallback_model
        )

    recovery_events.append(
        RecoveryEvent(stage="extraction", action="safe_degradation",
                       detail="Both primary and fallback models failed; degrading to deterministic offline extraction.")
    )
    raw = extract_offline(brief)
    return ExtractionResult(raw, ExtractionMethod.SAFE_DEGRADATION, recovery_events, provider.name, None)
