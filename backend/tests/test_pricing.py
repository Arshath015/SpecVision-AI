from app.models.enums import (
    DesignCategory,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
    SettingType,
)
from app.models.schemas import InventoryCandidate, InventoryItem, InventoryMatchResult, ProductSpecification
from app.services.pricing import calculate_price


def _item() -> InventoryItem:
    return InventoryItem(
        product_id="SV-001", name="Test Ring", product_type="ring",
        design_category=DesignCategory.ENGAGEMENT_RING, metal_type=MetalType.GOLD,
        metal_purity=MetalPurity.K18, metal_color=MetalColor.YELLOW, setting_type=SettingType.PRONG,
        center_stone_type=GemstoneType.DIAMOND, center_stone_shape=GemstoneShape.OVAL,
        center_stone_carat_min=1.0, center_stone_carat_max=1.5,
        side_stone_type=GemstoneType.DIAMOND, side_stone_count=10,
        band_width_mm=2.0, unit_price=3000.0, currency="USD",
    )


def _candidate(item: InventoryItem, passed=True, score=0.9) -> InventoryCandidate:
    return InventoryCandidate(
        product_id=item.product_id, name=item.name, unit_price=item.unit_price, currency=item.currency,
        match_score=score, passed_threshold=passed, attribute_explanations=[], item=item,
    )


def test_no_reliable_match_yields_unavailable_price():
    match = InventoryMatchResult(candidates=[], selected=None, threshold_used=0.72, reliable_match_found=False, explanation="none")
    spec = ProductSpecification()
    result = calculate_price(spec, match)
    assert result.available is False
    assert result.indicative_total is None


def test_base_price_used_when_spec_within_catalog_range():
    item = _item()
    candidate = _candidate(item)
    match = InventoryMatchResult(candidates=[candidate], selected=candidate, threshold_used=0.72, reliable_match_found=True, explanation="ok")
    spec = ProductSpecification()
    spec.center_stone.carat.value = 1.2  # within [1.0, 1.5]
    spec.side_stones.count_total.value = 10  # equals catalog count
    result = calculate_price(spec, match)
    assert result.available is True
    assert result.indicative_total == item.unit_price
    assert result.is_confirmed_quote is False


def test_carat_upcharge_applied_above_catalog_range():
    item = _item()
    candidate = _candidate(item)
    match = InventoryMatchResult(candidates=[candidate], selected=candidate, threshold_used=0.72, reliable_match_found=True, explanation="ok")
    spec = ProductSpecification()
    spec.center_stone.gemstone_type.value = GemstoneType.DIAMOND
    spec.center_stone.carat.value = 2.0  # 0.5ct above catalog max of 1.5
    result = calculate_price(spec, match)
    assert result.indicative_total > item.unit_price
    codes = [a.code for a in result.assumptions]
    assert "CARAT_UPCHARGE_APPLIED" in codes


def test_side_stone_adjustment_applied_above_catalog_count():
    item = _item()
    candidate = _candidate(item)
    match = InventoryMatchResult(candidates=[candidate], selected=candidate, threshold_used=0.72, reliable_match_found=True, explanation="ok")
    spec = ProductSpecification()
    spec.side_stones.count_total.value = 20  # 10 more than catalog's 10
    result = calculate_price(spec, match)
    assert result.indicative_total == item.unit_price + 10 * 35.0
    codes = [a.code for a in result.assumptions]
    assert "SIDE_STONE_COUNT_ADJUSTED" in codes


def test_unknown_carat_does_not_apply_upcharge():
    item = _item()
    candidate = _candidate(item)
    match = InventoryMatchResult(candidates=[candidate], selected=candidate, threshold_used=0.72, reliable_match_found=True, explanation="ok")
    spec = ProductSpecification()  # carat unknown
    result = calculate_price(spec, match)
    assert result.indicative_total == item.unit_price
    codes = [a.code for a in result.assumptions]
    assert "CARAT_UNKNOWN_NO_UPCHARGE" in codes
