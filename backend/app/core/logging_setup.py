"""Structured logging configuration.

Logs request id, latency, extraction outcome, provider/model, recovery
events, matching outcome, CV result, and review status -- but never raw
API keys, image bytes, or full brief text (only brief length).
"""
from __future__ import annotations

import logging

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
