"""Pydantic v2 schemas shared across extraction, matching, CV, pricing and
the public API response. Keeping every contract in one module makes the
end-to-end response shape easy to audit against the brief.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.enums import (
    ConfidenceLevel,
    CVMethod,
    DesignCategory,
    ExtractionMethod,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
    ProductType,
    ReviewSeverity,
    SettingType,
    SourceType,
)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic attributed-value wrapper
# ---------------------------------------------------------------------------
class AttributedValue(BaseModel, Generic[T]):
    """A single extracted field, honest about where it came from and how
    sure the system is. ``value`` is ``None`` when the attribute is unknown
    — never fabricated.
    """

    value: T | None = None
    source: SourceType = SourceType.UNKNOWN
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    reason: str = "No evidence available for this field."


# ---------------------------------------------------------------------------
# Extracted specification
# ---------------------------------------------------------------------------
class DimensionSpec(BaseModel):
    ring_size_us: AttributedValue[float] = Field(default_factory=AttributedValue)
    band_width_mm: AttributedValue[float] = Field(default_factory=AttributedValue)


class CenterStoneSpec(BaseModel):
    gemstone_type: AttributedValue[GemstoneType] = Field(default_factory=AttributedValue)
    shape: AttributedValue[GemstoneShape] = Field(default_factory=AttributedValue)
    carat: AttributedValue[float] = Field(default_factory=AttributedValue)


class SideStoneSpec(BaseModel):
    gemstone_type: AttributedValue[GemstoneType] = Field(default_factory=AttributedValue)
    shape: AttributedValue[GemstoneShape] = Field(default_factory=AttributedValue)
    count_total: AttributedValue[int] = Field(default_factory=AttributedValue)
    total_carat: AttributedValue[float] = Field(default_factory=AttributedValue)


class ProductSpecification(BaseModel):
    """The structured ring specification produced by the extraction stage."""

    product_type: AttributedValue[ProductType] = Field(default_factory=AttributedValue)
    design_category: AttributedValue[DesignCategory] = Field(default_factory=AttributedValue)
    metal_type: AttributedValue[MetalType] = Field(default_factory=AttributedValue)
    metal_purity: AttributedValue[MetalPurity] = Field(default_factory=AttributedValue)
    metal_color: AttributedValue[MetalColor] = Field(default_factory=AttributedValue)
    setting_type: AttributedValue[SettingType] = Field(default_factory=AttributedValue)
    dimensions: DimensionSpec = Field(default_factory=DimensionSpec)
    center_stone: CenterStoneSpec = Field(default_factory=CenterStoneSpec)
    side_stones: SideStoneSpec = Field(default_factory=SideStoneSpec)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
class InventoryItem(BaseModel):
    product_id: str
    name: str
    product_type: ProductType
    design_category: DesignCategory
    metal_type: MetalType
    metal_purity: MetalPurity
    metal_color: MetalColor
    setting_type: SettingType
    center_stone_type: GemstoneType
    center_stone_shape: GemstoneShape
    center_stone_carat_min: float
    center_stone_carat_max: float
    side_stone_type: GemstoneType
    side_stone_count: int
    band_width_mm: float
    unit_price: float
    currency: str = "USD"


class AttributeMatchExplanation(BaseModel):
    attribute: str
    extracted_value: str
    inventory_value: str
    weight: float
    attribute_score: float
    status: str  # "exact_match" | "partial_match" | "contradiction" | "missing_data"
    explanation: str


class InventoryCandidate(BaseModel):
    product_id: str
    name: str
    unit_price: float
    currency: str
    match_score: float
    passed_threshold: bool
    attribute_explanations: list[AttributeMatchExplanation]
    item: InventoryItem


class InventoryMatchResult(BaseModel):
    candidates: list[InventoryCandidate]
    selected: InventoryCandidate | None
    threshold_used: float
    reliable_match_found: bool
    explanation: str


# ---------------------------------------------------------------------------
# Computer vision
# ---------------------------------------------------------------------------
class CVDetection(BaseModel):
    x: int
    y: int
    radius: int
    detection_source: str  # "hough_circle" | "contour"


class CVEstimate(BaseModel):
    method: CVMethod
    available: bool
    estimated_visible_count: int | None = None
    detections: list[CVDetection] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    reason: str = ""
    image_quality_warnings: list[str] = Field(default_factory=list)
    suitable_for_automatic_use: bool = False
    annotated_image_base64: str | None = None
    processing_time_ms: float = 0.0
    brief_claimed_count: int | None = None
    disagreement_with_brief: bool = False
    disagreement_ratio: float | None = None


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------
class PriceAssumption(BaseModel):
    code: str
    description: str


class PriceEstimate(BaseModel):
    available: bool
    currency: str = "USD"
    base_unit_price: float | None = None
    adjustments: list[dict] = Field(default_factory=list)
    indicative_total: float | None = None
    formula_description: str = ""
    assumptions: list[PriceAssumption] = Field(default_factory=list)
    is_confirmed_quote: bool = False
    reason: str = ""


# ---------------------------------------------------------------------------
# Confidence & review
# ---------------------------------------------------------------------------
class ReviewFlag(BaseModel):
    code: str
    severity: ReviewSeverity
    message: str
    recommended_action: str


class ConfidenceSummary(BaseModel):
    overall_status: str  # "auto_approved" | "needs_review" | "failed"
    low_confidence_fields: list[str] = Field(default_factory=list)
    review_flags: list[ReviewFlag] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Processing metadata
# ---------------------------------------------------------------------------
class RecoveryEvent(BaseModel):
    stage: str
    action: str
    detail: str


class ProcessingMetadata(BaseModel):
    request_id: str
    app_mode: str  # "offline" | "live"
    extraction_method: ExtractionMethod
    provider: str | None = None
    model_used: str | None = None
    total_latency_ms: float
    extraction_latency_ms: float
    cv_latency_ms: float
    matching_latency_ms: float
    recovery_events: list[RecoveryEvent] = Field(default_factory=list)
    estimated_llm_cost_usd: float | None = None


# ---------------------------------------------------------------------------
# Top-level response
# ---------------------------------------------------------------------------
class AnalyzeResponse(BaseModel):
    specification: ProductSpecification
    inventory_match: InventoryMatchResult
    cv_estimate: CVEstimate
    price_estimate: PriceEstimate
    confidence_summary: ConfidenceSummary
    processing_metadata: ProcessingMetadata


class HealthResponse(BaseModel):
    status: str
    app_mode: str
    llm_provider: str | None
    primary_model: str | None
    live_mode_ready: bool
    inventory_items_loaded: int
