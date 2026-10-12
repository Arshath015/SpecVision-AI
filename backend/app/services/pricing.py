"""Deterministic indicative pricing.

Formula (documented, no hidden logic):
  indicative_total = catalog_unit_price
                      + extra_carat_adjustment   (only if spec carat > catalog max)
                      + extra_side_stone_adjustment  (only if spec count > catalog count)

This is deliberately conservative: it never discounts below the matched
catalog item's price, and every adjustment line is recorded with the
exact numbers used so the estimate is auditable. If no inventory
candidate passed the matching threshold, no defensible base price exists
and the result is returned as unavailable rather than guessed.
"""
from __future__ import annotations

from app.core.pricing_config import (
    CARAT_ADJUSTMENT_TOLERANCE,
    DEFAULT_EXTRA_CARAT_RATE,
    EXTRA_CARAT_RATE_BY_STONE,
    EXTRA_SIDE_STONE_RATE,
    SIDE_STONE_COUNT_ADJUSTMENT_TOLERANCE,
)
from app.models.schemas import InventoryMatchResult, PriceAssumption, PriceEstimate, ProductSpecification


def calculate_price(spec: ProductSpecification, match: InventoryMatchResult) -> PriceEstimate:
    if not match.reliable_match_found or match.selected is None:
        return PriceEstimate(
            available=False,
            reason=(
                "No inventory candidate met the auto-selection matching threshold, so there is no "
                "defensible catalog reference to price from. An indicative price would be a guess."
            ),
        )

    item = match.selected.item
    currency = item.currency
    base_price = item.unit_price
    adjustments: list[dict] = []
    assumptions: list[PriceAssumption] = [
        PriceAssumption(
            code="CATALOG_BASE_PRICE",
            description=f"Base price taken from matched catalog item {item.product_id} ({item.name}).",
        )
    ]

    carat = spec.center_stone.carat.value
    if carat is None:
        assumptions.append(PriceAssumption(
            code="CARAT_UNKNOWN_NO_UPCHARGE",
            description="Center stone carat was not determined; no carat upcharge was applied (base catalog price used as-is).",
        ))
    else:
        excess = carat - item.center_stone_carat_max
        if excess > CARAT_ADJUSTMENT_TOLERANCE:
            stone_type = spec.center_stone.gemstone_type.value
            rate = EXTRA_CARAT_RATE_BY_STONE.get(stone_type.value if stone_type else "", DEFAULT_EXTRA_CARAT_RATE)
            amount = round(excess * rate, 2)
            adjustments.append({
                "label": "Center stone carat upcharge",
                "detail": f"{excess:.2f}ct above catalog max {item.center_stone_carat_max}ct at ${rate:.0f}/ct",
                "amount": amount,
            })
            assumptions.append(PriceAssumption(
                code="CARAT_UPCHARGE_APPLIED",
                description=f"Extra {excess:.2f}ct beyond the catalog item's range was charged at an illustrative ${rate:.0f}/ct rate.",
            ))

    side_count = spec.side_stones.count_total.value
    if side_count is None:
        assumptions.append(PriceAssumption(
            code="SIDE_COUNT_UNKNOWN_NO_ADJUSTMENT",
            description="Side stone count was not determined; no per-stone adjustment was applied.",
        ))
    else:
        excess_stones = side_count - item.side_stone_count
        if excess_stones > SIDE_STONE_COUNT_ADJUSTMENT_TOLERANCE:
            amount = round(excess_stones * EXTRA_SIDE_STONE_RATE, 2)
            adjustments.append({
                "label": "Additional side stones",
                "detail": f"{excess_stones} stone(s) beyond catalog count {item.side_stone_count} at ${EXTRA_SIDE_STONE_RATE:.0f}/stone",
                "amount": amount,
            })
            assumptions.append(PriceAssumption(
                code="SIDE_STONE_COUNT_ADJUSTED",
                description=f"{excess_stones} extra side stone(s) beyond the catalog item were charged at an illustrative ${EXTRA_SIDE_STONE_RATE:.0f}/stone rate.",
            ))

    total = round(base_price + sum(a["amount"] for a in adjustments), 2)

    if not match.selected.passed_threshold:
        # Defensive: should not happen since reliable_match_found implies passed, but keep explicit.
        pass

    return PriceEstimate(
        available=True,
        currency=currency,
        base_unit_price=base_price,
        adjustments=adjustments,
        indicative_total=total,
        formula_description=(
            "indicative_total = catalog_unit_price + extra_carat_adjustment(if spec carat exceeds "
            "catalog max) + extra_side_stone_adjustment(if spec side count exceeds catalog count)"
        ),
        assumptions=assumptions,
        is_confirmed_quote=False,
        reason="Indicative estimate derived from the best-matching catalog item; not a confirmed commercial quote.",
    )
