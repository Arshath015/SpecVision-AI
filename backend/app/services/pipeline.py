"""End-to-end orchestration for POST /analyze.

Wires together extraction -> specification building -> plausibility
checks -> computer vision -> inventory matching -> pricing -> confidence
summary -> processing metadata. Each stage is independently testable;
this module only sequences them and measures latency.
"""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.models.enums import ExtractionMethod
from app.models.schemas import AnalyzeResponse, ProcessingMetadata
from app.services.confidence import build_confidence_summary, cross_check_cv_vs_brief, run_plausibility_checks
from app.services.cv_pipeline import estimate_visible_components
from app.services.extraction import extract_specification_raw
from app.services.inventory import load_inventory
from app.services.matching import match_inventory
from app.services.pricing import calculate_price
from app.services.specification_builder import build_specification


def run_analysis(brief: str, image_bytes: bytes | None, request_id: str) -> AnalyzeResponse:
    settings = get_settings()
    total_start = time.perf_counter()

    extract_start = time.perf_counter()
    extraction_result = extract_specification_raw(brief)
    extraction_latency_ms = (time.perf_counter() - extract_start) * 1000

    spec = build_specification(extraction_result.raw, brief, extraction_result.method)
    plausibility_flags = run_plausibility_checks(spec)

    cv_start = time.perf_counter()
    cv_estimate = estimate_visible_components(image_bytes)
    cv_latency_ms = (time.perf_counter() - cv_start) * 1000
    cv_disagreement_flag = cross_check_cv_vs_brief(spec, cv_estimate)

    match_start = time.perf_counter()
    catalog = load_inventory()
    match = match_inventory(spec, catalog)
    matching_latency_ms = (time.perf_counter() - match_start) * 1000

    price = calculate_price(spec, match)

    confidence_summary = build_confidence_summary(
        spec, match, cv_estimate, price, plausibility_flags, cv_disagreement_flag,
        extraction_result.recovery_events, extraction_result.method,
    )

    total_latency_ms = (time.perf_counter() - total_start) * 1000

    is_live_call = extraction_result.method in (
        ExtractionMethod.LLM_LIVE, ExtractionMethod.LLM_LIVE_FALLBACK_MODEL, ExtractionMethod.LLM_REPAIRED,
    )
    metadata = ProcessingMetadata(
        request_id=request_id,
        app_mode=settings.app_mode,
        extraction_method=extraction_result.method,
        provider=extraction_result.provider,
        model_used=extraction_result.model_used,
        total_latency_ms=round(total_latency_ms, 2),
        extraction_latency_ms=round(extraction_latency_ms, 2),
        cv_latency_ms=round(cv_latency_ms, 2),
        matching_latency_ms=round(matching_latency_ms, 2),
        recovery_events=extraction_result.recovery_events,
        estimated_llm_cost_usd=0.0 if is_live_call else None,
    )

    return AnalyzeResponse(
        specification=spec,
        inventory_match=match,
        cv_estimate=cv_estimate,
        price_estimate=price,
        confidence_summary=confidence_summary,
        processing_metadata=metadata,
    )
