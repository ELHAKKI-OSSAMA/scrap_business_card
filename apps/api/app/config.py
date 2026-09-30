from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (see .env.example).
    Secrets have no usable defaults in production."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "Multilingual OCR Suite API"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./dev.db"
    redis_url: str | None = None

    # auth
    jwt_secret: str = Field(default="dev-only-change-me-dev-only-change-me", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    allow_registration: bool = True
    password_min_length: int = 10

    # CORS (web apps are served through the same nginx origin in Docker; dev servers need CORS)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://localhost:5174"]

    # uploads
    max_upload_mb: int = 15
    max_image_pixels: int = 60_000_000
    malware_scanner: Literal["none", "clamav"] = "none"
    clamav_host: str = "clamav"
    clamav_port: int = 3310

    # storage
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "./data/storage"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "ocr-suite"
    s3_region: str = "us-east-1"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    # jobs
    job_execution: Literal["celery", "thread", "sync"] = "thread"

    # OCR
    ocr_provider: Literal["paddleocr", "tesseract"] = "paddleocr"
    ocr_fallback_provider: Literal["tesseract", "none"] = "tesseract"
    ocr_device: str = "cpu"  # cpu | gpu:0
    ocr_det_model: str = "PP-OCRv5_mobile_det"
    ocr_use_orientation_model: bool = True
    ocr_warmup: bool = False

    # extraction
    default_phone_region: str | None = None  # e.g. "MA" – only used if explicitly configured
    llm_provider: Literal["none", "openai_compatible"] = "none"
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_timeout_s: float = 60.0

    # optional machine translation (separate feature, always labelled machine-generated)
    translation_provider: Literal["none", "libretranslate"] = "none"
    translation_url: str | None = None
    translation_api_key: str | None = None

    # rate limiting
    rate_limit_auth_per_minute: int = 10
    rate_limit_upload_per_minute: int = 60

    # retention
    deleted_retention_days: int = 30
    document_retention_days: int = 0  # 0 = keep until deleted

    metrics_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider != "none" and bool(self.llm_base_url and self.llm_model)

    def check_production(self) -> None:
        if self.environment == "production":
            if "dev-only" in self.jwt_secret:
                raise RuntimeError("JWT_SECRET must be set in production")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Use PostgreSQL in production")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.check_production()
    return s
