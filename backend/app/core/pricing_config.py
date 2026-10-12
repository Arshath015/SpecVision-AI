"""Centralized, documented pricing assumptions.

All figures here are illustrative placeholders for this evaluation
project, not verified market data. They exist so the pricing formula in
app/services/pricing.py has no unexplained magic numbers.
"""
from __future__ import annotations

# Per-carat upcharge applied ONLY to the portion of the center stone carat
# that exceeds the matched catalog item's carat range maximum. We never
# discount for a smaller-than-catalog stone -- the catalog unit price is
# treated as a floor, consistent with "indicative, not a confirmed quote".
EXTRA_CARAT_RATE_BY_STONE: dict[str, float] = {
    "diamond": 2800.0,
    "sapphire": 950.0,
    "ruby": 1050.0,
    "emerald": 1000.0,
    "moissanite": 480.0,
    "morganite": 320.0,
    "aquamarine": 280.0,
    "amethyst": 190.0,
    "topaz": 220.0,
    "pearl": 160.0,
    "other": 320.0,
}
DEFAULT_EXTRA_CARAT_RATE = 300.0

# Per-stone cost applied ONLY to side stones beyond the matched catalog
# item's side_stone_count -- mirrors the side-stone cost component baked
# into the illustrative catalog prices (see backend/scripts/generate_inventory.py).
EXTRA_SIDE_STONE_RATE = 35.0

# A carat/count difference within this tolerance is treated as "close
# enough to the catalog item" and does not trigger an adjustment line --
# avoids implying false precision for a hand-finished custom product.
CARAT_ADJUSTMENT_TOLERANCE = 0.05
SIDE_STONE_COUNT_ADJUSTMENT_TOLERANCE = 1
