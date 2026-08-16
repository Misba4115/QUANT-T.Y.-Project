"""Validated, cached application settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_JWT_SECRETS = {
    "change-me-in-production",
    "your-secret-key-here-change-this-in-production",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    quant_env: Literal["development", "test", "production"] = "development"
    app_name: str = "QUANT API"
    api_prefix: str = "/api"
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_key: str | None = None

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    session_cookie_name: str = "quant_session"
    session_cookie_domain: str | None = None
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    google_client_id: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    llm_provider: Literal["gemini", "openai"] = "gemini"
    openai_api_key: str | None = None

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "quant_public_knowledge_v1"
    qdrant_vector_size: int = Field(default=384, ge=128, le=4096)

    market_data_timeout_seconds: float = Field(default=8.0, gt=0, le=30)
    coingecko_api_key: str | None = None
    credential_encryption_key: str | None = None
    public_app_url: str = "http://localhost:3000"
    upstox_client_id: str | None = None
    upstox_client_secret: str | None = None
    upstox_redirect_uri: str = "http://localhost:8000/api/connectors/upstox/callback"
    inbox_webhook_secret: str | None = None
    inbox_domain: str = "inbox.quant.local"
    export_signing_secret: str | None = None
    worker_poll_seconds: int = Field(default=30, ge=5, le=3600)
    guardian_min_history: int = Field(default=10, ge=3, le=1000)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    max_import_rows: int = Field(default=10_000, ge=1, le=100_000)

    @field_validator("frontend_origins")
    @classmethod
    def disallow_wildcard_origins(cls, value: str) -> str:
        if "*" in value:
            raise ValueError("FRONTEND_ORIGINS cannot contain '*' when credentials are enabled")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]

    @property
    def supabase_runtime_key(self) -> str | None:
        return self.supabase_secret_key or self.supabase_service_role_key or self.supabase_key

    @property
    def database_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_runtime_key)

    @property
    def session_cookie_secure(self) -> bool:
        return self.quant_env == "production"

    def validate_runtime_security(self) -> None:
        if self.quant_env == "production" and self.jwt_secret_key in DEFAULT_JWT_SECRETS:
            raise RuntimeError("JWT_SECRET_KEY must be replaced before production startup")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime_security()
    return settings


def clear_settings_cache() -> None:
    get_settings.cache_clear()
