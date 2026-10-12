from app.models.enums import ConfidenceLevel, CVMethod
from app.services.cv_pipeline import estimate_visible_components


def test_no_image_returns_unavailable():
    result = estimate_visible_components(None)
    assert result.available is False
    assert result.method == CVMethod.UNAVAILABLE
    assert result.estimated_visible_count is None


def test_corrupt_bytes_returns_unavailable():
    result = estimate_visible_components(b"this is not image data")
    assert result.available is False


def test_too_small_image_returns_unavailable(sample_image_bytes):
    result = estimate_visible_components(sample_image_bytes("ring_tiny_resolution.jpg"))
    assert result.available is False
    assert "resolution" in result.reason.lower()


def test_clear_image_detects_plausible_stone_count(sample_image_bytes):
    result = estimate_visible_components(sample_image_bytes("ring_clear_6stones.jpg"))
    assert result.available is True
    assert result.method == CVMethod.CONTOUR_AND_HOUGH
    assert result.estimated_visible_count is not None
    assert result.estimated_visible_count > 0
    assert result.annotated_image_base64


def test_no_side_stones_image_reports_zero(sample_image_bytes):
    result = estimate_visible_components(sample_image_bytes("ring_no_sidestones.jpg"))
    assert result.available is True
    assert result.estimated_visible_count == 0


def test_blurry_image_flags_low_confidence_and_quality_warning(sample_image_bytes):
    result = estimate_visible_components(sample_image_bytes("ring_blurry_10stones.jpg"))
    assert result.available is True
    assert result.confidence == ConfidenceLevel.LOW
    assert any("blur" in w.lower() for w in result.image_quality_warnings)
    assert result.suitable_for_automatic_use is False


def test_result_never_claims_count_without_image():
    result = estimate_visible_components(None)
    assert result.estimated_visible_count is None
    assert result.suitable_for_automatic_use is False
