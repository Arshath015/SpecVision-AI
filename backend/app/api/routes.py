"""HTTP routes. Business logic lives in app/services/*; this module only
handles request validation, content negotiation, and error translation.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.core.image_validation import sniff_image_content_type
from app.core.logging_setup import get_logger
from app.models.schemas import AnalyzeResponse, HealthResponse, InventoryItem
from app.services.inventory import get_item, load_inventory
from app.services.pipeline import run_analysis

router = APIRouter()
logger = get_logger("specvision.api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_mode=settings.app_mode,
        llm_provider=settings.llm_provider if settings.is_live_mode else None,
        primary_model=settings.llm_primary_model if settings.is_live_mode else None,
        live_mode_ready=settings.live_mode_ready,
        inventory_items_loaded=len(load_inventory()),
    )


@router.get("/inventory", response_model=list[InventoryItem])
def list_inventory() -> list[InventoryItem]:
    return load_inventory()


@router.get("/inventory/{product_id}", response_model=InventoryItem)
def get_inventory_item(product_id: str) -> InventoryItem:
    item = get_item(product_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No inventory item with id '{product_id}'.")
    return item


async def _read_multipart(request: Request) -> tuple[str | None, bytes | None, str | None]:
    form = await request.form()
    brief = form.get("brief")
    brief = str(brief) if brief is not None else None
    image_field = form.get("image")
    image_bytes: bytes | None = None
    declared_type: str | None = None
    if image_field is not None and hasattr(image_field, "read"):
        image_bytes = await image_field.read()
        declared_type = getattr(image_field, "content_type", None)
    return brief, image_bytes, declared_type


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request) -> AnalyzeResponse:
    settings = get_settings()
    content_type = request.headers.get("content-type", "")

    image_bytes: bytes | None = None
    declared_type: str | None = None

    if content_type.startswith("application/json"):
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Request body is not valid JSON.") from exc
        brief = body.get("brief") if isinstance(body, dict) else None
    elif content_type.startswith("multipart/form-data"):
        brief, image_bytes, declared_type = await _read_multipart(request)
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported Content-Type. Use application/json (brief-only) or multipart/form-data (brief + optional image).",
        )

    if not brief or not isinstance(brief, str) or not brief.strip():
        raise HTTPException(status_code=422, detail="Field 'brief' is required and must be a non-empty string.")
    if len(brief) > 4000:
        raise HTTPException(status_code=422, detail="Field 'brief' exceeds the maximum length of 4000 characters.")

    if image_bytes:
        if len(image_bytes) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Image exceeds the maximum allowed size of {settings.max_image_size_bytes // (1024 * 1024)}MB.",
            )
        sniffed_type = sniff_image_content_type(image_bytes)
        if sniffed_type is None or sniffed_type not in settings.allowed_content_types_list:
            raise HTTPException(
                status_code=415,
                detail="Uploaded file is not a supported image format (JPEG, PNG, or WebP required).",
            )

    request_id = str(uuid.uuid4())
    try:
        result = run_analysis(brief=brief.strip(), image_bytes=image_bytes, request_id=request_id)
    except Exception:
        logger.exception("analyze_pipeline_failed request_id=%s", request_id)
        raise HTTPException(status_code=500, detail="Internal processing error. Please try again.") from None

    logger.info(
        "analyze_completed request_id=%s brief_len=%d has_image=%s extraction_method=%s "
        "review_status=%s total_latency_ms=%.1f",
        request_id, len(brief), bool(image_bytes),
        result.processing_metadata.extraction_method.value,
        result.confidence_summary.overall_status,
        result.processing_metadata.total_latency_ms,
    )
    return result
