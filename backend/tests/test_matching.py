from app.models.enums import (
    DesignCategory,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
    SettingType,
)
from app.models.schemas import InventoryItem, ProductSpecification
from app.services.matching import match_inventory


def _spec(**overrides) -> ProductSpecification:
    spec = ProductSpecification()
    if "metal_type" in overrides:
        spec.metal_type.value = overrides["metal_type"]
    if "metal_purity" in overrides:
        spec.metal_purity.value = overrides["metal_purity"]
    if "metal_color" in overrides:
        spec.metal_color.value = overrides["metal_color"]
    if "design_category" in overrides:
        spec.design_category.value = overrides["design_category"]
    if "setting_type" in overrides:
        spec.setting_type.value = overrides["setting_type"]
    if "center_stone_type" in overrides:
        spec.center_stone.gemstone_type.value = overrides["center_stone_type"]
    if "center_stone_shape" in overrides:
        spec.center_stone.shape.value = overrides["center_stone_shape"]
    if "carat" in overrides:
        spec.center_stone.carat.value = overrides["carat"]
    if "side_count" in overrides:
        spec.side_stones.count_total.value = overrides["side_count"]
    if "band_width" in overrides:
        spec.dimensions.band_width_mm.value = overrides["band_width"]
    return spec


def _item(product_id: str, **kw) -> InventoryItem:
    defaults = dict(
        name=f"Test item {product_id}",
        product_type="ring",
        design_category=DesignCategory.ENGAGEMENT_RING,
        metal_type=MetalType.GOLD,
        metal_purity=MetalPurity.K18,
        metal_color=MetalColor.YELLOW,
        setting_type=SettingType.PRONG,
        center_stone_type=GemstoneType.DIAMOND,
        center_stone_shape=GemstoneShape.OVAL,
        center_stone_carat_min=1.2,
        center_stone_carat_max=1.8,
        side_stone_type=GemstoneType.DIAMOND,
        side_stone_count=12,
        band_width_mm=2.0,
        unit_price=3000.0,
        currency="USD",
    )
    defaults.update(kw)
    return InventoryItem(product_id=product_id, **defaults)


def test_exact_match_scores_high_and_passes_threshold():
    spec = _spec(
        metal_type=MetalType.GOLD, metal_purity=MetalPurity.K18, metal_color=MetalColor.YELLOW,
        design_category=DesignCategory.ENGAGEMENT_RING, setting_type=SettingType.PRONG,
        center_stone_type=GemstoneType.DIAMOND, center_stone_shape=GemstoneShape.OVAL,
        carat=1.5, side_count=12, band_width=2.0,
    )
    catalog = [_item("SV-001")]
    result = match_inventory(spec, catalog)
    assert result.reliable_match_found
    assert result.selected.product_id == "SV-001"
    assert result.selected.match_score > 0.95


def test_contradiction_lowers_score():
    spec = _spec(metal_type=MetalType.SILVER, center_stone_type=GemstoneType.SAPPHIRE)
    matching_item = _item("SV-001", metal_type=MetalType.SILVER, center_stone_type=GemstoneType.SAPPHIRE)
    contradicting_item = _item("SV-002", metal_type=MetalType.GOLD, center_stone_type=GemstoneType.DIAMOND)
    result = match_inventory(spec, [matching_item, contradicting_item])
    scores = {c.product_id: c.match_score for c in result.candidates}
    # SV-001 matches metal_type and center_stone_type exactly; SV-002
    # contradicts both -- it must score strictly lower.
    assert scores["SV-002"] < scores["SV-001"]


def test_missing_attributes_do_not_crash_and_use_neutral_scoring():
    spec = ProductSpecification()  # everything unknown
    catalog = [_item("SV-001"), _item("SV-002", unit_price=4000.0)]
    result = match_inventory(spec, catalog)
    assert len(result.candidates) == 2
    # Identical attributes except price -> identical match scores.
    assert result.candidates[0].match_score == result.candidates[1].match_score


def test_deterministic_ordering_and_tie_breaking():
    spec = _spec(metal_type=MetalType.GOLD)
    identical_a = _item("SV-010", metal_type=MetalType.GOLD)
    identical_b = _item("SV-002", metal_type=MetalType.GOLD)
    result_1 = match_inventory(spec, [identical_a, identical_b])
    result_2 = match_inventory(spec, [identical_b, identical_a])
    # Same scores regardless of input order; lower product_id wins ties.
    assert [c.product_id for c in result_1.candidates] == ["SV-002", "SV-010"]
    assert [c.product_id for c in result_2.candidates] == ["SV-002", "SV-010"]


def test_same_input_always_produces_same_ranking_and_scores():
    spec = _spec(metal_type=MetalType.PLATINUM, center_stone_type=GemstoneType.RUBY, carat=2.0)
    catalog = [_item(f"SV-{i:03d}", unit_price=1000.0 + i) for i in range(5)]
    first = match_inventory(spec, catalog)
    second = match_inventory(spec, catalog)
    assert [(c.product_id, c.match_score) for c in first.candidates] == [
        (c.product_id, c.match_score) for c in second.candidates
    ]


def test_threshold_blocks_auto_selection_when_no_good_candidate():
    spec = _spec(metal_type=MetalType.SILVER, center_stone_type=GemstoneType.PEARL, design_category=DesignCategory.WEDDING_BAND)
    catalog = [_item("SV-001", metal_type=MetalType.GOLD, center_stone_type=GemstoneType.DIAMOND, design_category=DesignCategory.ENGAGEMENT_RING)]
    result = match_inventory(spec, catalog)
    assert not result.reliable_match_found
    assert result.selected is None
    assert len(result.candidates) == 1


def test_top_three_candidates_returned_when_available():
    spec = _spec(metal_type=MetalType.GOLD)
    catalog = [_item(f"SV-{i:03d}") for i in range(10)]
    result = match_inventory(spec, catalog)
    assert len(result.candidates) == 3
