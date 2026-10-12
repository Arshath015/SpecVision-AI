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
