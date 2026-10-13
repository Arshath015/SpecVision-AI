"""Centralized runtime configuration.

Every tunable value referenced elsewhere in the backend (matching weights,
thresholds, retry limits, file size caps) is defined here so the rest of the
codebase never hardcodes a magic number. Values come from environment
variables / a local .env file and fall back to documented defaults.
"""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Runtime mode -----------------------------------------------------
    # "offline" never calls an external LLM API; "live" requires an API key.
    app_mode: str = "offline"

    # --- LLM provider -------------------------------------------------------
    # "groq" (OpenAI-compatible chat completions) is supported out of the box.
    # Swap llm_provider/model names via .env -- no code change required for
    # another OpenAI-compatible provider.
    llm_provider: str = "groq"
    llm_primary_model: str = "openai/gpt-oss-120b"
    llm_fallback_model: str = "openai/gpt-oss-20b"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_request_timeout_seconds: float = 20.0
    llm_max_retries: int = 2

    # --- CORS ---------------------------------------------------------------
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Uploads --------------------------------------------------------------
    max_image_size_bytes: int = 8 * 1024 * 1024
    allowed_image_content_types: str = "image/jpeg,image/png,image/webp"

    # --- Matching -------------------------------------------------------------
    match_auto_select_threshold: float = 0.72
    match_top_n: int = 3

    # --- Confidence / review ---------------------------------------------------
    cv_vs_brief_disagreement_ratio: float = 0.4  # relative diff that triggers review
    low_confidence_review_threshold: str = "low"

    # --- Pricing --------------------------------------------------------------
    default_currency: str = "USD"

    # --- Server -----------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    # External path prefix stripped by a reverse proxy in front of this app
    # (e.g. "/api" on the Vercel deployment, where the Services routing
    # layer strips "/api" before FastAPI sees the request). Empty locally
    # and in Docker, where the app is reached directly with no prefix.
    # Without this, FastAPI's auto-generated Swagger UI hardcodes
    # "/openapi.json" as an absolute, unprefixed path, which 404s (or in
    # a multi-service deployment, silently resolves to a different
    # service entirely) once the app is actually reached at "/api/*".
    root_path: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def allowed_content_types_list(self) -> list[str]:
        return [c.strip() for c in self.allowed_image_content_types.split(",") if c.strip()]

    @property
    def is_live_mode(self) -> bool:
        return self.app_mode.lower() == "live"

    @property
    def live_mode_ready(self) -> bool:
        """True only if live mode is requested AND a key is actually configured."""
        if self.llm_provider == "groq":
            return self.is_live_mode and bool(self.groq_api_key)
        return self.is_live_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
