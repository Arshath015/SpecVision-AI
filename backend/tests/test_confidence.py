from app.models.enums import ConfidenceLevel, CVMethod, GemstoneType, MetalPurity, MetalType
from app.models.schemas import CVEstimate, ProductSpecification
from app.services.confidence import cross_check_cv_vs_brief, run_plausibility_checks


def test_implausible_carat_is_flagged_and_downgraded():
    spec = ProductSpecification()
    spec.center_stone.carat.value = 50.0  # absurd for a ring
    spec.center_stone.carat.confidence = ConfidenceLevel.HIGH
    flags = run_plausibility_checks(spec)
    assert any(f.code == "IMPLAUSIBLE_CENTER_CARAT" for f in flags)
    assert spec.center_stone.carat.confidence == ConfidenceLevel.LOW


def test_metal_type_purity_contradiction_is_flagged():
    spec = ProductSpecification()
    spec.metal_type.value = MetalType.SILVER
    spec.metal_purity.value = MetalPurity.K18  # a gold purity, contradicts silver
    flags = run_plausibility_checks(spec)
    assert any(f.code == "METAL_TYPE_PURITY_CONTRADICTION" for f in flags)


def test_consistent_metal_type_and_purity_raises_no_flag():
    spec = ProductSpecification()
    spec.metal_type.value = MetalType.GOLD
    spec.metal_purity.value = MetalPurity.K18
    flags = run_plausibility_checks(spec)
    assert not any(f.code == "METAL_TYPE_PURITY_CONTRADICTION" for f in flags)


def test_plausible_values_raise_no_flags():
    spec = ProductSpecification()
    spec.center_stone.carat.value = 1.5
    spec.dimensions.ring_size_us.value = 7.0
    spec.dimensions.band_width_mm.value = 2.0
    spec.side_stones.count_total.value = 12
    flags = run_plausibility_checks(spec)
    assert flags == []


def test_cv_brief_disagreement_detected_above_threshold():
    spec = ProductSpecification()
    spec.side_stones.count_total.value = 20
    cv = CVEstimate(method=CVMethod.CONTOUR_AND_HOUGH, available=True, estimated_visible_count=4, confidence=ConfidenceLevel.HIGH)
    flag = cross_check_cv_vs_brief(spec, cv)
    assert flag is not None
    assert flag.code == "CV_BRIEF_COUNT_DISAGREEMENT"
    assert cv.disagreement_with_brief is True


def test_cv_brief_agreement_raises_no_flag():
    spec = ProductSpecification()
    spec.side_stones.count_total.value = 12
    cv = CVEstimate(method=CVMethod.CONTOUR_AND_HOUGH, available=True, estimated_visible_count=11, confidence=ConfidenceLevel.HIGH)
    flag = cross_check_cv_vs_brief(spec, cv)
    assert flag is None
    assert cv.disagreement_with_brief is False


def test_cv_unavailable_skips_disagreement_check():
    spec = ProductSpecification()
    spec.side_stones.count_total.value = 12
    cv = CVEstimate(method=CVMethod.UNAVAILABLE, available=False)
    flag = cross_check_cv_vs_brief(spec, cv)
    assert flag is None
