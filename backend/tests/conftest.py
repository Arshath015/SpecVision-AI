"""The standard test suite never touches the network or a real API key.
Every test starts in offline mode with no provider key configured;
individual tests that exercise the live-mode code path explicitly
monkeypatch the provider's HTTP call instead of making a real request.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core import config as config_module

IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation" / "images" / "synthetic"


@pytest.fixture(autouse=True)
def _offline_by_default(monkeypatch):
    monkeypatch.setenv("APP_MODE", "offline")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


@pytest.fixture
def live_mode_with_key(monkeypatch):
    """Switch settings to live mode with a dummy key -- callers must still
    mock the provider's HTTP call; this fixture never hits the network.
    """
    monkeypatch.setenv("APP_MODE", "live")
    monkeypatch.setenv("GROQ_API_KEY", "test-dummy-key")
    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


@pytest.fixture
def sample_image_bytes():
    def _load(name: str) -> bytes:
        return (IMAGES_DIR / name).read_bytes()
    return _load
