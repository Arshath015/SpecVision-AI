"""HTTP routes. Business logic lives in app/services/*; this module only
handles request validation, content negotiation, and error translation.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# Pydantic binds the base Starlette class (not FastAPI's UploadFile
# subclass) when UploadFile appears inside a Union -- see the "image"
# parameter below. isinstance() must check against this base class or a
# real upload silently fails the check.
from starlette.datastructures import UploadFile as StarletteUploadFile

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


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze a jewelry sales brief, with an optional reference photo",
    description=(
        "Accepts `multipart/form-data` with a required `brief` text field and an "
        "optional `image` file upload (JPEG, PNG, or WebP). For a brief-only request, "
        "submit the form with no `image` part -- there is no separate JSON content type "
        "for this endpoint, so the request body always declares correctly in OpenAPI/Swagger."
    ),
)
async def analyze(
    brief: str = Form(
        ...,
        min_length=1,
        max_length=4000,
        description="Free-text sales brief describing the desired jewelry piece.",
    ),
    # UploadFile | str | None (not just UploadFile | None): when an optional
    # file field is left empty, some multipart clients -- including Swagger
    # UI's "Send empty value" checkbox, left checked by default -- submit an
    # empty string instead of omitting the part entirely. A strict
    # `UploadFile | None` annotation rejects that with a 422 even though "no
    # file" is exactly what the client meant; accepting `str` here and
    # treating it as "no image" below handles that real client behavior
    # instead of fighting it.
    image: UploadFile | str | None = File(
        default=None,
        description="Optional reference photo (JPEG, PNG, or WebP, max size configured server-side).",
    ),
) -> AnalyzeResponse:
    settings = get_settings()

    if not brief.strip():
        raise HTTPException(status_code=422, detail="Field 'brief' is required and must be a non-empty string.")

    image_bytes: bytes | None = None
    if isinstance(image, StarletteUploadFile) and image.filename:
        image_bytes = await image.read()

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
