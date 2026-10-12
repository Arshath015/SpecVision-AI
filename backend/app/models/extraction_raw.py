"""Strict schema for the LLM's raw JSON output.

The model is asked to extract attribute *values* only -- never asked to
invent its own confidence score (per project policy, confidence is always
computed deterministically downstream). Pydantic validation here is what
rejects malformed JSON, wrong types, invalid enum values, and implausible
quantities before anything reaches the rest of the pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    DesignCategory,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
    ProductType,
    SettingType,
)


class RawExtraction(BaseModel):
    model_config = {"extra": "forbid"}

    product_type: ProductType | None = None
    design_category: DesignCategory | None = None
    metal_type: MetalType | None = None
    metal_purity: MetalPurity | None = None
    metal_color: MetalColor | None = None
    setting_type: SettingType | None = None

    # Bounds here are a syntactic sanity net against LLM hallucination
    # (negative numbers, typos like 5000 instead of 0.5) -- NOT the domain
    # plausibility judgment. A user-stated value that is unusual but
    # numerically well-formed (e.g. "a 50 carat diamond") must still pass
    # through so app.services.confidence's deterministic plausibility
    # checks can flag it for human review. Tighter, ring-specific bounds
    # live there (see CARAT_PLAUSIBLE_MAX etc. in app/services/confidence.py).
    ring_size_us: float | None = Field(default=None, ge=0, le=50)
    band_width_mm: float | None = Field(default=None, gt=0, le=50)

    center_stone_type: GemstoneType | None = None
    center_stone_shape: GemstoneShape | None = None
    center_stone_carat: float | None = Field(default=None, gt=0, le=200)

    side_stone_type: GemstoneType | None = None
    side_stone_shape: GemstoneShape | None = None
    side_stone_count_total: int | None = Field(default=None, ge=0, le=300)
    side_stone_total_carat: float | None = Field(default=None, ge=0, le=200)

    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def _truncate_notes(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return v[:500]
