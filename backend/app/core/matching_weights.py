"""Centralized configuration for deterministic inventory matching.

Rationale for weight allocation (sums to 1.0):

- ``center_stone_type`` (0.20) and ``design_category`` (0.15) dominate
  because they define what kind of product this fundamentally is -- a
  sapphire halo ring is not a reasonable substitute for a diamond
  solitaire regardless of how closely other attributes line up.
- ``setting_type`` (0.10), ``center_stone_shape`` (0.10) and
  ``center_stone_carat`` (0.10) are the next tier: they strongly affect
  visual identity and price but a customer could plausibly accept a
  close variant (e.g. cushion vs. princess cut).
- ``metal_type`` (0.10) matters more than ``metal_purity`` (0.05) and
  ``metal_color`` (0.05) individually, since the raw metal changes cost
  structure the most, while purity/color are easier to special-order.
- ``side_stone_count`` (0.08) and ``side_stone_type`` (0.04) matter less
  than the center stone because side stones are frequently
  interchangeable in custom work.
- ``band_width_mm`` (0.03) is a minor refinement -- adjustable by a
  jeweler with little cost impact, so it gets the smallest weight.

Why deterministic (no LLM) matching: the same specification and catalog
must always produce the same ranking so results are repeatable, every
score is explainable attribute-by-attribute, there is no per-request API
cost, and evaluation runs are reproducible byte-for-byte.
"""
from __future__ import annotations

ATTRIBUTE_WEIGHTS: dict[str, float] = {
    "center_stone_type": 0.20,
    "design_category": 0.15,
    "setting_type": 0.10,
    "center_stone_shape": 0.10,
    "center_stone_carat": 0.10,
    "metal_type": 0.10,
    "metal_purity": 0.05,
    "metal_color": 0.05,
    "side_stone_count": 0.08,
    "side_stone_type": 0.04,
    "band_width_mm": 0.03,
}

assert abs(sum(ATTRIBUTE_WEIGHTS.values()) - 1.0) < 1e-9, "Matching weights must sum to 1.0"

# Numeric tolerance bands used when deciding exact / partial / contradiction
# for continuous attributes. These are deliberately documented constants,
# not hidden magic numbers.
CARAT_PARTIAL_RELATIVE_TOLERANCE = 0.25   # within 25% of range edge -> partial
CARAT_CONTRADICTION_RELATIVE_GAP = 0.6    # beyond 60% of range edge -> contradiction

SIDE_STONE_COUNT_EXACT_TOLERANCE = 0      # must match exactly for "exact"
SIDE_STONE_COUNT_PARTIAL_TOLERANCE = 4    # within +/-4 stones -> partial
SIDE_STONE_COUNT_CONTRADICTION_GAP = 10   # beyond +/-10 stones -> contradiction

BAND_WIDTH_EXACT_TOLERANCE_MM = 0.3
BAND_WIDTH_PARTIAL_TOLERANCE_MM = 1.0

MISSING_DATA_NEUTRAL_SCORE = 0.5
