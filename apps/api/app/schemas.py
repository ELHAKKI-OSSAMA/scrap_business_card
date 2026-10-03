from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = {}
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


# ---------------------------------------------------------------- auth
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    display_name: str | None = Field(default=None, max_length=120)
    locale: Literal["en", "fr", "ar"] = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    locale: str
    default_phone_region: str | None
    workspace_id: uuid.UUID
    workspace_name: str
    role: str
    android_app_url: str | None = None  # effective link: workspace setting, else server default


class WorkspaceSettingsIn(BaseModel):
    android_app_url: str | None = Field(default=None, max_length=500, description="https link to the Android app (APK or store page); empty = server default")


class MeUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    locale: Literal["en", "fr", "ar"] | None = None
    default_phone_region: str | None = Field(default=None, description="ISO 3166-1 alpha-2, used only for numbers without an international prefix")

    @field_validator("default_phone_region")
    @classmethod
    def _iso(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        if len(v) != 2 or not v.isalpha():
            raise ValueError("must be a 2-letter ISO country code")
        return v.upper()


# ---------------------------------------------------------------- documents
class DocumentCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)
    client_ref: str | None = Field(default=None, min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$", description="Idempotency key (offline clients). Replays return the existing document.")


class DocumentMetaUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)
    favorite: bool | None = None


class BulkIdsIn(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=500)


class ImageOut(BaseModel):
    side: str
    mime: str
    width: int
    height: int
    processed_width: int | None
    processed_height: int | None
    size_bytes: int
    sha256: str
    url: str
    processed_url: str | None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    error_code: str | None
    error_message: str | None
    provider: str | None
    model_metadata: list | None
    preprocessing: dict | None
    quality: dict | None
    processing_ms: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    options: dict | None


class OcrLineOut(BaseModel):
    id: str
    side: str
    text: str | None
    normalized_text: str | None
    bbox: dict
    polygon: list | None
    confidence: float | None
    script: str | None
    language: str | None
    direction: str | None
    model: str | None
    block_index: int | None
    line_index: int | None
    extra: dict | None


class RegionOut(BaseModel):
    id: str
    side: str
    label: str | None
    bbox: dict
    confidence: float | None
    method: str | None
    line_ids: list[str] = []


class OcrPageOut(BaseModel):
    side: str
    width: int | None
    height: int | None
    lines: list[OcrLineOut]
    regions: list[RegionOut]


class DocumentOut(BaseModel):
    id: uuid.UUID
    product: str
    client_ref: str | None
    title: str | None
    notes: str | None
    status: str
    review_status: str
    favorite: bool = False
    version: int
    languages: list[str] | None
    data: dict | None
    machine_data: dict | None = None
    images: list[ImageOut]
    latest_job: JobOut | None
    ocr: list[OcrPageOut] | None = None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None


class DocumentSummary(BaseModel):
    id: uuid.UUID
    product: str
    title: str | None
    status: str
    review_status: str
    favorite: bool = False
    languages: list[str] | None
    summary: dict[str, Any]
    sides: list[str]
    created_at: datetime
    updated_at: datetime


class Page(BaseModel):
    items: list[DocumentSummary]
    total: int
    page: int
    page_size: int


class ProcessIn(BaseModel):
    languages: list[Literal["ar", "fr", "en"]] | None = Field(default=None, description="Restrict candidate recognizers; default = all (mixed documents)")
    provider: Literal["paddleocr", "tesseract"] | None = None
    use_llm: bool = Field(default=False, description="Only honoured when an LLM is configured server-side")
    default_phone_region: str | None = Field(default=None, min_length=2, max_length=2)
    force: bool = Field(default=False, description="Re-run even if an identical job already exists")


class JobAccepted(BaseModel):
    job_id: uuid.UUID
    status: str
    document_id: uuid.UUID
    reused: bool = False


class FieldChange(BaseModel):
    path: str = Field(max_length=200, pattern=r"^[a-z_]+(\.[a-z0-9_]+)*$")
    op: Literal["set", "append", "remove", "verify"] = "set"
    value: Any = None


class FieldsPatch(BaseModel):
    changes: list[FieldChange] = Field(min_length=1, max_length=100)
    expected_version: int | None = None


class ReviewIn(BaseModel):
    status: Literal["verified", "needs_review", "rejected", "unreviewed"]
    note: str | None = Field(default=None, max_length=500)


class ReviewEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    action: str
    path: str | None
    old_value: Any
    new_value: Any
    note: str | None
    user_id: uuid.UUID | None
    created_at: datetime


class DuplicateOut(BaseModel):
    document: DocumentSummary
    matched_keys: list[str]
    score: float


class MergeIn(BaseModel):
    other_id: uuid.UUID
    confirm: bool = Field(description="Must be true: merges are never automatic")


class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source: Literal["ar", "fr", "en", "auto"] = "auto"
    target: Literal["ar", "fr", "en"]


class TranslateOut(BaseModel):
    translated_text: str
    machine_generated: bool = True
    provider: str
    source: str
    target: str
