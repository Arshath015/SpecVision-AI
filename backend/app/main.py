from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_setup import configure_logging, get_logger

configure_logging()
logger = get_logger("specvision.app")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "specvision_startup app_mode=%s live_mode_ready=%s llm_provider=%s",
        settings.app_mode, settings.live_mode_ready, settings.llm_provider,
    )
    yield


app = FastAPI(
    title="SpecVision AI",
    description="AI-powered product specification and cost estimation for custom jewelry.",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
