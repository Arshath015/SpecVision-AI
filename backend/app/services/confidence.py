"""Deterministic plausibility checks, cross-source disagreement detection,
and the human-review flag policy.

Design principle (per project policy): confidence is never something we
ask the LLM to self-report. It is always derived here from concrete,
inspectable evidence -- schema validation having already passed, whether
a value was stated vs. inferred, whether a plausibility rule failed, and
whether independent evidence sources (brief vs. CV) agree.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.models.enums import ConfidenceLevel, ExtractionMethod, MetalPurity, MetalType, ReviewSeverity
from app.models.schemas import (
    ConfidenceSummary,
    CVEstimate,
    InventoryMatchResult,
    PriceEstimate,
    ProductSpecification,
    RecoveryEvent,
    ReviewFlag,
)

_VALID_PURITIES_BY_METAL: dict[MetalType, set[MetalPurity]] = {
    MetalType.GOLD: {MetalPurity.K10, MetalPurity.K14, MetalPurity.K18, MetalPurity.K22, MetalPurity.K24},
    MetalType.PLATINUM: {MetalPurity.PLATINUM_950},
    MetalType.SILVER: {MetalPurity.SILVER_925},
}

CARAT_PLAUSIBLE_MAX = 15.0
RING_SIZE_PLAUSIBLE_RANGE = (3.0, 15.0)
BAND_WIDTH_PLAUSIBLE_RANGE = (0.5, 12.0)
SIDE_STONE_COUNT_PLAUSIBLE_MAX = 120


def run_plausibility_checks(spec: ProductSpecification) -> list[ReviewFlag]:
    """Downgrades field confidence in-place when a deterministic rule
    fails, and returns the corresponding review flags.
    """
    flags: list[ReviewFlag] = []

    carat = spec.center_stone.carat
    if carat.value is not None and (carat.value <= 0 or carat.value > CARAT_PLAUSIBLE_MAX):
        carat.confidence = ConfidenceLevel.LOW
        carat.reason = f"Carat value {carat.value} is outside the plausible range (0, {CARAT_PLAUSIBLE_MAX}]."
        flags.append(ReviewFlag(
            code="IMPLAUSIBLE_CENTER_CARAT", severity=ReviewSeverity.CRITICAL,
            message=f"Center stone carat ({carat.value}) is implausible for a ring.",
            recommended_action="Confirm the intended carat weight with the customer before pricing or matching.",
        ))

    ring_size = spec.dimensions.ring_size_us
    if ring_size.value is not None and not (RING_SIZE_PLAUSIBLE_RANGE[0] <= ring_size.value <= RING_SIZE_PLAUSIBLE_RANGE[1]):
        ring_size.confidence = ConfidenceLevel.LOW
        ring_size.reason = f"Ring size {ring_size.value} is outside the plausible US size range {RING_SIZE_PLAUSIBLE_RANGE}."
        flags.append(ReviewFlag(
            code="IMPLAUSIBLE_RING_SIZE", severity=ReviewSeverity.WARNING,
            message=f"Ring size ({ring_size.value}) is outside the typical US size range.",
            recommended_action="Verify the ring size with the customer.",
        ))

    band_width = spec.dimensions.band_width_mm
    if band_width.value is not None and not (BAND_WIDTH_PLAUSIBLE_RANGE[0] <= band_width.value <= BAND_WIDTH_PLAUSIBLE_RANGE[1]):
        band_width.confidence = ConfidenceLevel.LOW
        band_width.reason = f"Band width {band_width.value}mm is outside the plausible range {BAND_WIDTH_PLAUSIBLE_RANGE}mm."
        flags.append(ReviewFlag(
            code="IMPLAUSIBLE_BAND_WIDTH", severity=ReviewSeverity.WARNING,
            message=f"Band width ({band_width.value}mm) looks implausible.",
            recommended_action="Verify the intended band width with the customer.",
        ))

    side_count = spec.side_stones.count_total
    if side_count.value is not None and side_count.value > SIDE_STONE_COUNT_PLAUSIBLE_MAX:
        side_count.confidence = ConfidenceLevel.LOW
        side_count.reason = f"Side stone count {side_count.value} exceeds the plausible maximum ({SIDE_STONE_COUNT_PLAUSIBLE_MAX})."
        flags.append(ReviewFlag(
            code="IMPLAUSIBLE_SIDE_STONE_COUNT", severity=ReviewSeverity.WARNING,
            message=f"Side stone count ({side_count.value}) is unusually high.",
            recommended_action="Confirm the side stone count with the customer.",
        ))

    metal_type_val = spec.metal_type.value
    purity_val = spec.metal_purity.value
    if metal_type_val is not None and purity_val is not None:
        valid = _VALID_PURITIES_BY_METAL.get(metal_type_val)
        if valid is not None and purity_val not in valid:
            spec.metal_purity.confidence = ConfidenceLevel.LOW
            spec.metal_purity.reason = f"Purity '{purity_val.value}' is not a valid purity for metal type '{metal_type_val.value}'."
            flags.append(ReviewFlag(
                code="METAL_TYPE_PURITY_CONTRADICTION", severity=ReviewSeverity.CRITICAL,
                message=f"Metal type '{metal_type_val.value}' and purity '{purity_val.value}' are contradictory.",
                recommended_action="Clarify the intended metal and purity with the customer before matching or pricing.",
            ))

    return flags


def cross_check_cv_vs_brief(spec: ProductSpecification, cv: CVEstimate) -> ReviewFlag | None:
    """Compares the CV visible-count estimate against the side-stone count
    stated/inferred from the brief, using a documented disagreement ratio
    rather than an arbitrary hidden rule.
    """
    brief_count = spec.side_stones.count_total.value
    cv.brief_claimed_count = brief_count

    if brief_count is None or not cv.available or cv.estimated_visible_count is None:
        return None

    settings = get_settings()
    denom = max(brief_count, 1)
    ratio = abs(cv.estimated_visible_count - brief_count) / denom
    cv.disagreement_ratio = round(ratio, 3)
    cv.disagreement_with_brief = ratio > settings.cv_vs_brief_disagreement_ratio

    if cv.disagreement_with_brief:
        return ReviewFlag(
            code="CV_BRIEF_COUNT_DISAGREEMENT", severity=ReviewSeverity.WARNING,
            message=(
                f"CV detected {cv.estimated_visible_count} visible component(s) vs. "
                f"{brief_count} implied by the brief (relative difference {ratio:.0%})."
            ),
            recommended_action="Review the reference image and brief together; the visible count may be partial due to occlusion, or the brief may overstate the design.",
        )
    return None


def _collect_low_confidence_fields(spec: ProductSpecification) -> list[str]:
    low: list[str] = []
    checks = [
        ("product_type", spec.product_type),
        ("design_category", spec.design_category),
        ("metal_type", spec.metal_type),
        ("metal_purity", spec.metal_purity),
        ("metal_color", spec.metal_color),
        ("setting_type", spec.setting_type),
        ("dimensions.ring_size_us", spec.dimensions.ring_size_us),
        ("dimensions.band_width_mm", spec.dimensions.band_width_mm),
        ("center_stone.gemstone_type", spec.center_stone.gemstone_type),
        ("center_stone.shape", spec.center_stone.shape),
        ("center_stone.carat", spec.center_stone.carat),
        ("side_stones.gemstone_type", spec.side_stones.gemstone_type),
        ("side_stones.count_total", spec.side_stones.count_total),
    ]
    for path, attr in checks:
        if attr.confidence == ConfidenceLevel.LOW:
            low.append(path)
    return low


_PRICING_CRITICAL_FIELDS = {"center_stone.gemstone_type", "center_stone.carat", "side_stones.count_total", "metal_type"}


def build_confidence_summary(
    spec: ProductSpecification,
    match: InventoryMatchResult,
    cv: CVEstimate,
    price: PriceEstimate,
    plausibility_flags: list[ReviewFlag],
    cv_disagreement_flag: ReviewFlag | None,
    recovery_events: list[RecoveryEvent],
    extraction_method: ExtractionMethod,
) -> ConfidenceSummary:
    flags: list[ReviewFlag] = list(plausibility_flags)
    if cv_disagreement_flag:
        flags.append(cv_disagreement_flag)

    low_fields = _collect_low_confidence_fields(spec)
    pricing_relevant_low = [f for f in low_fields if f in _PRICING_CRITICAL_FIELDS]
    if pricing_relevant_low:
        flags.append(ReviewFlag(
            code="INCOMPLETE_SPEC_FOR_PRICING", severity=ReviewSeverity.WARNING,
            message=f"Specification is missing or uncertain in fields that affect pricing: {', '.join(pricing_relevant_low)}.",
            recommended_action="Collect the missing details from the customer before issuing a firm quote.",
        ))

    if not match.reliable_match_found:
        flags.append(ReviewFlag(
            code="NO_RELIABLE_INVENTORY_MATCH", severity=ReviewSeverity.WARNING,
            message=match.explanation,
            recommended_action="Treat the top candidates as reference points only; consider a custom quote.",
        ))

    if cv.available and (cv.image_quality_warnings or not cv.suitable_for_automatic_use):
        flags.append(ReviewFlag(
            code="IMAGE_QUALITY_INSUFFICIENT", severity=ReviewSeverity.WARNING,
            message="Image quality or detection stability is insufficient for an automatic visible-stone count.",
            recommended_action="Request a clearer, well-lit, closer photo of the reference piece if an exact visible count matters.",
        ))
    elif not cv.available:
        flags.append(ReviewFlag(
            code="CV_UNAVAILABLE", severity=ReviewSeverity.INFO,
            message=cv.reason,
            recommended_action="Provide a reference image if a visible-stone estimate is needed.",
        ))

    if extraction_method == ExtractionMethod.SAFE_DEGRADATION:
        flags.append(ReviewFlag(
            code="EXTRACTION_DEGRADED", severity=ReviewSeverity.CRITICAL,
            message="Live model extraction failed; the system safely degraded to offline rule-based extraction.",
            recommended_action="Re-run once the LLM provider is reachable, or manually verify the specification.",
        ))
    elif extraction_method in (ExtractionMethod.LLM_REPAIRED, ExtractionMethod.LLM_LIVE_FALLBACK_MODEL):
        flags.append(ReviewFlag(
            code="EXTRACTION_RECOVERED", severity=ReviewSeverity.INFO,
            message=f"Extraction succeeded only after recovery ({extraction_method.value}).",
            recommended_action="No action required; shown for transparency.",
        ))

    if not price.available:
        flags.append(ReviewFlag(
            code="PRICE_UNAVAILABLE", severity=ReviewSeverity.WARNING,
            message=price.reason,
            recommended_action="A defensible indicative price requires a reliable inventory match.",
        ))

    actionable_flags = [f for f in flags if f.severity != ReviewSeverity.INFO]
    nothing_usable = (
        len(low_fields) >= 10 and not match.reliable_match_found and not cv.available
    )
    if nothing_usable:
        overall_status = "failed"
    elif actionable_flags:
        overall_status = "needs_review"
    else:
        overall_status = "auto_approved"

    return ConfidenceSummary(
        overall_status=overall_status,
        low_confidence_fields=low_fields,
        review_flags=flags,
    )
