from app.models.enums import (
    DesignCategory,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
)
from app.services.extraction import extract_specification_raw
from app.models.enums import ExtractionMethod


def test_offline_mode_used_when_app_mode_offline():
    result = extract_specification_raw("A simple silver ring.")
    assert result.method == ExtractionMethod.OFFLINE_FIXTURE
    assert result.provider is None


def test_example_brief_extracts_expected_fields():
    brief = (
        "I need a custom 18K yellow-gold engagement ring with an oval center diamond, "
        "six small stones on each side, approximately a 1.5-carat center stone, and a slim band."
    )
    result = extract_specification_raw(brief)
    raw = result.raw
    assert raw.metal_type == MetalType.GOLD
    assert raw.metal_purity == MetalPurity.K18
    assert raw.metal_color == MetalColor.YELLOW
    assert raw.design_category == DesignCategory.ENGAGEMENT_RING
    assert raw.center_stone_type == GemstoneType.DIAMOND
    assert raw.center_stone_shape == GemstoneShape.OVAL
    assert raw.center_stone_carat == 1.5
    assert raw.side_stone_count_total == 12


def test_vague_brief_leaves_fields_unknown_rather_than_guessed():
    result = extract_specification_raw("Something nice please.")
    raw = result.raw
    assert raw.metal_type is None
    assert raw.center_stone_type is None
    assert raw.center_stone_carat is None


def test_offline_extraction_is_deterministic():
    brief = "14k white gold halo ring with a round moissanite, 2.0 carat."
    first = extract_specification_raw(brief)
    second = extract_specification_raw(brief)
    assert first.raw == second.raw


def test_side_stone_type_is_not_confused_with_center_stone_type():
    # Regression test: the side-stone-type extractor used to do a
    # whole-text keyword search, so it would grab "diamond" (the center
    # stone, mentioned first) instead of "moissanite" (the actual side
    # stone type) whenever both appeared in the same brief.
    brief = (
        "A solitaire ring in 18k yellow gold with a round diamond center stone, "
        "about 0.45 carats, tension setting, eight moissanite side stones, band width 1.7mm."
    )
    result = extract_specification_raw(brief)
    raw = result.raw
    assert raw.center_stone_type == GemstoneType.DIAMOND
    assert raw.side_stone_type == GemstoneType.MOISSANITE
