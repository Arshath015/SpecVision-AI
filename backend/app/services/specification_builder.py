"""Converts a validated ``RawExtraction`` into a full ``ProductSpecification``
with explicit source attribution and a first-pass confidence rating per
field. Cross-field plausibility checks (which can *downgrade* these
confidences) live in app/services/confidence.py, run afterward.
"""
from __future__ import annotations

from enum import Enum

from app.models.enums import ConfidenceLevel, ExtractionMethod, SourceType
from app.models.extraction_raw import RawExtraction
from app.models.schemas import AttributedValue, CenterStoneSpec, DimensionSpec, ProductSpecification, SideStoneSpec


def _value_mentioned_literally(value: Enum | float | int | None, brief_lower: str) -> bool:
    if value is None:
        return False
    token = value.value if isinstance(value, Enum) else str(value)
    token = token.replace("_", " ").lower()
    return token in brief_lower


def _attribute(value, brief_lower: str, extraction_method: ExtractionMethod, field_label: str) -> AttributedValue:
    if value is None:
        return AttributedValue(
            value=None, source=SourceType.UNKNOWN, confidence=ConfidenceLevel.LOW,
            reason=f"{field_label} was not stated in the brief and could not be confidently inferred.",
        )

    if extraction_method == ExtractionMethod.OFFLINE_FIXTURE:
        # The offline extractor only ever returns values it matched
        # literally against the brief text via keyword/regex rules.
        return AttributedValue(
            value=value, source=SourceType.USER_PROVIDED, confidence=ConfidenceLevel.HIGH,
            reason=f"{field_label} matched directly in the brief text by the offline rule-based extractor.",
        )

    if _value_mentioned_literally(value, brief_lower):
        return AttributedValue(
            value=value, source=SourceType.USER_PROVIDED, confidence=ConfidenceLevel.HIGH,
            reason=f"{field_label} is explicitly stated in the brief.",
        )

    return AttributedValue(
        value=value, source=SourceType.MODEL_INFERRED, confidence=ConfidenceLevel.MEDIUM,
        reason=f"{field_label} was inferred by the extraction model from context; not an exact quote from the brief.",
    )


def build_specification(raw: RawExtraction, brief: str, extraction_method: ExtractionMethod) -> ProductSpecification:
    brief_lower = brief.lower()

    return ProductSpecification(
        product_type=_attribute(raw.product_type, brief_lower, extraction_method, "Product type"),
        design_category=_attribute(raw.design_category, brief_lower, extraction_method, "Design category"),
        metal_type=_attribute(raw.metal_type, brief_lower, extraction_method, "Metal type"),
        metal_purity=_attribute(raw.metal_purity, brief_lower, extraction_method, "Metal purity"),
        metal_color=_attribute(raw.metal_color, brief_lower, extraction_method, "Metal color"),
        setting_type=_attribute(raw.setting_type, brief_lower, extraction_method, "Setting type"),
        dimensions=DimensionSpec(
            ring_size_us=_attribute(raw.ring_size_us, brief_lower, extraction_method, "Ring size"),
            band_width_mm=_attribute(raw.band_width_mm, brief_lower, extraction_method, "Band width"),
        ),
        center_stone=CenterStoneSpec(
            gemstone_type=_attribute(raw.center_stone_type, brief_lower, extraction_method, "Center stone type"),
            shape=_attribute(raw.center_stone_shape, brief_lower, extraction_method, "Center stone shape"),
            carat=_attribute(raw.center_stone_carat, brief_lower, extraction_method, "Center stone carat"),
        ),
        side_stones=SideStoneSpec(
            gemstone_type=_attribute(raw.side_stone_type, brief_lower, extraction_method, "Side stone type"),
            shape=_attribute(raw.side_stone_shape, brief_lower, extraction_method, "Side stone shape"),
            count_total=_attribute(raw.side_stone_count_total, brief_lower, extraction_method, "Side stone count"),
            total_carat=_attribute(raw.side_stone_total_carat, brief_lower, extraction_method, "Side stone total carat"),
        ),
        notes=raw.notes,
    )
