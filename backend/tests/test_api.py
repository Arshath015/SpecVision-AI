from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import AnalyzeResponse

client = TestClient(app)

EXAMPLE_BRIEF = (
    "I need a custom 18K yellow-gold engagement ring with an oval center diamond, "
    "six small stones on each side, approximately a 1.5-carat center stone, and a slim band."
)


def test_health_endpoint_reports_offline_mode():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app_mode"] == "offline"
    assert body["live_mode_ready"] is False
    assert body["inventory_items_loaded"] >= 30


def test_inventory_list_and_get():
    r = client.get("/inventory")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 30
    first_id = items[0]["product_id"]

    r2 = client.get(f"/inventory/{first_id}")
    assert r2.status_code == 200
    assert r2.json()["product_id"] == first_id

    r3 = client.get("/inventory/NOT-A-REAL-ID")
    assert r3.status_code == 404


def test_analyze_brief_only_json_request():
    r = client.post("/analyze", json={"brief": EXAMPLE_BRIEF})
    assert r.status_code == 200
    body = r.json()
    parsed = AnalyzeResponse.model_validate(body)  # full schema contract check
    assert parsed.processing_metadata.extraction_method.value == "offline_fixture"
    assert parsed.processing_metadata.app_mode == "offline"
    assert parsed.cv_estimate.available is False


def test_analyze_with_image_multipart():
    import pathlib
    img_path = pathlib.Path(__file__).resolve().parent.parent.parent / "evaluation" / "images" / "synthetic" / "ring_clear_6stones.jpg"
    img_bytes = img_path.read_bytes()
    r = client.post("/analyze", data={"brief": EXAMPLE_BRIEF}, files={"image": ("ring.jpg", img_bytes, "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["cv_estimate"]["available"] is True
    assert body["cv_estimate"]["estimated_visible_count"] is not None
    assert body["cv_estimate"]["annotated_image_base64"]


def test_analyze_rejects_empty_brief():
    r = client.post("/analyze", json={"brief": "   "})
    assert r.status_code == 422


def test_analyze_rejects_missing_brief_field():
    r = client.post("/analyze", json={})
    assert r.status_code == 422


def test_analyze_rejects_invalid_image_content():
    r = client.post("/analyze", data={"brief": "test ring"}, files={"image": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 415


def test_analyze_rejects_unsupported_content_type():
    r = client.post("/analyze", content=b"plain text", headers={"content-type": "text/plain"})
    assert r.status_code == 415


def test_analyze_rejects_oversized_image(monkeypatch):
    from app.core import config as config_module
    monkeypatch.setenv("MAX_IMAGE_SIZE_BYTES", "100")
    config_module.get_settings.cache_clear()
    oversized = b"\xff\xd8\xff" + b"0" * 200
    r = client.post("/analyze", data={"brief": "test ring"}, files={"image": ("x.jpg", oversized, "image/jpeg")})
    assert r.status_code == 413
    config_module.get_settings.cache_clear()


def test_analyze_response_matches_documented_schema_end_to_end():
    r = client.post("/analyze", json={"brief": "14k white gold halo ring, round moissanite, 1.0 carat, 8 side stones."})
    assert r.status_code == 200
    parsed = AnalyzeResponse.model_validate(r.json())
    assert parsed.inventory_match.threshold_used > 0
    assert parsed.confidence_summary.overall_status in {"auto_approved", "needs_review", "failed"}
    assert parsed.processing_metadata.request_id
