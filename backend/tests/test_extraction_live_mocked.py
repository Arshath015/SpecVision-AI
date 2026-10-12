"""Live-mode extraction logic, fully mocked -- no real network call is
made anywhere in this file. These tests specifically cover malformed
model output, bounded retries, model fallback, and safe degradation.
"""
from __future__ import annotations

import itertools

import pytest

from app.models.enums import ExtractionMethod
from app.services.extraction import extract_specification_raw
from app.services.llm.base import LLMProviderError
from app.services.llm.groq_provider import GroqProvider

VALID_JSON = '{"product_type": "ring", "metal_type": "gold", "metal_purity": "14k"}'
MALFORMED_JSON = "{ this is not valid json "
INVALID_ENUM_JSON = '{"metal_type": "unobtainium"}'


def _patch_sequence(monkeypatch, responses):
    """responses: list of either a string to return, or an Exception instance to raise."""
    it = iter(responses)

    def fake_generate_json(self, system_prompt, user_prompt, model):
        item = next(it)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(GroqProvider, "generate_json", fake_generate_json)


def test_malformed_json_on_first_attempt_is_repaired_on_retry(live_mode_with_key, monkeypatch):
    _patch_sequence(monkeypatch, [MALFORMED_JSON, VALID_JSON])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.LLM_REPAIRED
    assert result.raw.metal_type.value == "gold"
    assert any(e.action == "json_repaired" for e in result.recovery_events)


def test_invalid_enum_value_is_rejected_and_retried(live_mode_with_key, monkeypatch):
    _patch_sequence(monkeypatch, [INVALID_ENUM_JSON, VALID_JSON])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.LLM_REPAIRED
    assert any(e.action == "invalid_model_output" for e in result.recovery_events)


def test_primary_exhausted_falls_back_to_secondary_model(live_mode_with_key, monkeypatch):
    # Primary gets 2 bad attempts (matches default llm_max_retries=2), fallback succeeds.
    _patch_sequence(monkeypatch, [MALFORMED_JSON, MALFORMED_JSON, VALID_JSON])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.LLM_LIVE_FALLBACK_MODEL
    assert any(e.action == "primary_model_exhausted" for e in result.recovery_events)


def test_both_models_failing_degrades_safely_to_offline(live_mode_with_key, monkeypatch):
    _patch_sequence(monkeypatch, [MALFORMED_JSON, MALFORMED_JSON, MALFORMED_JSON])
    result = extract_specification_raw("18k yellow gold ring.")
    assert result.method == ExtractionMethod.SAFE_DEGRADATION
    assert any(e.action == "safe_degradation" for e in result.recovery_events)
    # Safe degradation still returns a usable, validated result (offline rules).
    assert result.raw.metal_type.value == "gold"


def test_provider_timeout_triggers_retry_then_fallback(live_mode_with_key, monkeypatch):
    timeout_error = LLMProviderError("Groq request timed out after 20.0s")
    _patch_sequence(monkeypatch, [timeout_error, timeout_error, VALID_JSON])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.LLM_LIVE_FALLBACK_MODEL
    assert any("timed out" in e.detail for e in result.recovery_events)


def test_empty_model_response_is_handled_without_crashing(live_mode_with_key, monkeypatch):
    _patch_sequence(monkeypatch, ["", "", ""])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.SAFE_DEGRADATION


def test_clean_success_on_first_attempt_records_no_recovery_events(live_mode_with_key, monkeypatch):
    _patch_sequence(monkeypatch, [VALID_JSON])
    result = extract_specification_raw("A gold ring.")
    assert result.method == ExtractionMethod.LLM_LIVE
    assert result.recovery_events == []
