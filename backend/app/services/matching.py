"""Deterministic, explainable inventory matching.

No LLM is involved anywhere in this module. Given an extracted
``ProductSpecification`` and the loaded inventory catalog, this computes a
weighted similarity score per candidate, with a per-attribute explanation,
and returns a stable top-N ranking.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.matching_weights import (
    ATTRIBUTE_WEIGHTS,
    BAND_WIDTH_EXACT_TOLERANCE_MM,
    BAND_WIDTH_PARTIAL_TOLERANCE_MM,
    CARAT_CONTRADICTION_RELATIVE_GAP,
    CARAT_PARTIAL_RELATIVE_TOLERANCE,
    MISSING_DATA_NEUTRAL_SCORE,
    SIDE_STONE_COUNT_CONTRADICTION_GAP,
    SIDE_STONE_COUNT_PARTIAL_TOLERANCE,
)
from app.models.schemas import (
    AttributeMatchExplanation,
    InventoryCandidate,
    InventoryItem,
    InventoryMatchResult,
    ProductSpecification,
)


def _categorical_score(extracted: str | None, candidate: str) -> tuple[float, str, str]:
    """Score a categorical attribute. Returns (score, status, extracted_str)."""
    if extracted is None or extracted == "unknown":
        return MISSING_DATA_NEUTRAL_SCORE, "missing_data", "unknown"
    if candidate == "unknown":
        return MISSING_DATA_NEUTRAL_SCORE, "missing_data", extracted
    if extracted == candidate:
        return 1.0, "exact_match", extracted
    return 0.0, "contradiction", extracted


def _carat_score(extracted: float | None, cmin: float, cmax: float) -> tuple[float, str]:
    if extracted is None:
        return MISSING_DATA_NEUTRAL_SCORE, "missing_data"
    if cmin <= extracted <= cmax:
        return 1.0, "exact_match"
    span = max(cmax - cmin, 0.1)
    gap = (cmin - extracted) if extracted < cmin else (extracted - cmax)
    relative_gap = gap / span
    if relative_gap <= CARAT_PARTIAL_RELATIVE_TOLERANCE:
        return 0.75, "partial_match"
    if relative_gap <= CARAT_CONTRADICTION_RELATIVE_GAP:
        return 0.35, "partial_match"
    return 0.0, "contradiction"


def _count_score(extracted: int | None, candidate: int) -> tuple[float, str]:
    if extracted is None:
        return MISSING_DATA_NEUTRAL_SCORE, "missing_data"
    diff = abs(extracted - candidate)
    if diff == 0:
        return 1.0, "exact_match"
    if diff <= SIDE_STONE_COUNT_PARTIAL_TOLERANCE:
        return 0.7, "partial_match"
    if diff <= SIDE_STONE_COUNT_CONTRADICTION_GAP:
        return 0.3, "partial_match"
    return 0.0, "contradiction"


def _width_score(extracted: float | None, candidate: float) -> tuple[float, str]:
    if extracted is None:
        return MISSING_DATA_NEUTRAL_SCORE, "missing_data"
    diff = abs(extracted - candidate)
    if diff <= BAND_WIDTH_EXACT_TOLERANCE_MM:
        return 1.0, "exact_match"
    if diff <= BAND_WIDTH_PARTIAL_TOLERANCE_MM:
        return 0.6, "partial_match"
    return 0.1, "contradiction"


def _score_candidate(spec: ProductSpecification, item: InventoryItem) -> InventoryCandidate:
    explanations: list[AttributeMatchExplanation] = []
    total = 0.0

    def add(attr: str, extracted_repr: str, inventory_repr: str, score: float, status: str, note: str) -> None:
        nonlocal total
        weight = ATTRIBUTE_WEIGHTS[attr]
        total += weight * score
        explanations.append(
            AttributeMatchExplanation(
                attribute=attr,
                extracted_value=extracted_repr,
                inventory_value=inventory_repr,
                weight=weight,
                attribute_score=round(score, 3),
                status=status,
                explanation=note,
            )
        )

    cs_type = spec.center_stone.gemstone_type.value.value if spec.center_stone.gemstone_type.value else None
    score, status, repr_val = _categorical_score(cs_type, item.center_stone_type.value)
    add("center_stone_type", repr_val, item.center_stone_type.value, score, status,
        f"Center stone type {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    design = spec.design_category.value.value if spec.design_category.value else None
    score, status, repr_val = _categorical_score(design, item.design_category.value)
    add("design_category", repr_val, item.design_category.value, score, status,
        f"Design category {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    setting = spec.setting_type.value.value if spec.setting_type.value else None
    score, status, repr_val = _categorical_score(setting, item.setting_type.value)
    add("setting_type", repr_val, item.setting_type.value, score, status,
        f"Setting type {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    shape = spec.center_stone.shape.value.value if spec.center_stone.shape.value else None
    score, status, repr_val = _categorical_score(shape, item.center_stone_shape.value)
    add("center_stone_shape", repr_val, item.center_stone_shape.value, score, status,
        f"Center stone shape {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    carat = spec.center_stone.carat.value
    score, status = _carat_score(carat, item.center_stone_carat_min, item.center_stone_carat_max)
    add("center_stone_carat", f"{carat}" if carat is not None else "unknown",
        f"{item.center_stone_carat_min}-{item.center_stone_carat_max}", score, status,
        f"Center carat {carat if carat is not None else 'unknown'} vs. catalog range "
        f"{item.center_stone_carat_min}-{item.center_stone_carat_max}ct.")

    metal = spec.metal_type.value.value if spec.metal_type.value else None
    score, status, repr_val = _categorical_score(metal, item.metal_type.value)
    add("metal_type", repr_val, item.metal_type.value, score, status,
        f"Metal type {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    purity = spec.metal_purity.value.value if spec.metal_purity.value else None
    score, status, repr_val = _categorical_score(purity, item.metal_purity.value)
    add("metal_purity", repr_val, item.metal_purity.value, score, status,
        f"Metal purity {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    color = spec.metal_color.value.value if spec.metal_color.value else None
    score, status, repr_val = _categorical_score(color, item.metal_color.value)
    add("metal_color", repr_val, item.metal_color.value, score, status,
        f"Metal color {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    side_count = spec.side_stones.count_total.value
    score, status = _count_score(side_count, item.side_stone_count)
    add("side_stone_count", f"{side_count}" if side_count is not None else "unknown",
        f"{item.side_stone_count}", score, status,
        f"Side stone count {side_count if side_count is not None else 'unknown'} vs. catalog {item.side_stone_count}.")

    side_type = spec.side_stones.gemstone_type.value.value if spec.side_stones.gemstone_type.value else None
    score, status, repr_val = _categorical_score(side_type, item.side_stone_type.value)
    add("side_stone_type", repr_val, item.side_stone_type.value, score, status,
        f"Side stone type {'matches' if status == 'exact_match' else status.replace('_', ' ')}.")

    width = spec.dimensions.band_width_mm.value
    score, status = _width_score(width, item.band_width_mm)
    add("band_width_mm", f"{width}" if width is not None else "unknown", f"{item.band_width_mm}", score, status,
        f"Band width {width if width is not None else 'unknown'}mm vs. catalog {item.band_width_mm}mm.")

    settings = get_settings()
    passed = total >= settings.match_auto_select_threshold
    return InventoryCandidate(
        product_id=item.product_id,
        name=item.name,
        unit_price=item.unit_price,
        currency=item.currency,
        match_score=round(total, 4),
        passed_threshold=passed,
        attribute_explanations=explanations,
        item=item,
    )


def match_inventory(spec: ProductSpecification, catalog: list[InventoryItem]) -> InventoryMatchResult:
    """Score every catalog item, rank descending by score with stable
    product_id tie-breaking, and return the top-N candidates.
    """
    settings = get_settings()
    scored = [_score_candidate(spec, item) for item in catalog]
    scored.sort(key=lambda c: (-c.match_score, c.product_id))

    top_n = scored[: settings.match_top_n]
    selected = top_n[0] if top_n and top_n[0].passed_threshold else None
    reliable = selected is not None

    if reliable:
        explanation = (
            f"Top candidate {selected.product_id} scored {selected.match_score:.2f}, "
            f"meeting the auto-selection threshold of {settings.match_auto_select_threshold:.2f}."
        )
    else:
        best = top_n[0].match_score if top_n else 0.0
        explanation = (
            f"No candidate reached the auto-selection threshold of "
            f"{settings.match_auto_select_threshold:.2f} (best score: {best:.2f}). "
            "A high similarity score does not prove exact product equivalence; "
            "results below threshold are shown for reference only and require human review."
        )

    return InventoryMatchResult(
        candidates=top_n,
        selected=selected,
        threshold_used=settings.match_auto_select_threshold,
        reliable_match_found=reliable,
        explanation=explanation,
    )
