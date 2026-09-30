"""Canonical data model.

Three kinds of information are kept apart everywhere:

* ``OcrLine.text``            – what the recognizer read (immutable, never rewritten)
* ``FieldValue.value``        – what extraction inferred / normalized (``extraction_method`` says how)
* ``review_status=corrected`` – what a human changed (the original machine value is kept in history)

Missing information is ``None``. Confidence is ``None`` when there is no meaningful estimate.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "QrFieldCheck",
    "Side",
    "Script",
    "Direction",
    "ExtractionMethod",
    "ReviewStatus",
    "BBox",
    "OcrLine",
    "QrCode",
    "CandidateRegion",
    "QualityReport",
    "PreprocessingStep",
    "ModelInfo",
    "OcrPage",
    "LanguageRegion",
    "FieldValue",
    "Address",
    "Phone",
    "BusinessCardExtraction",
    "SCHEMA_VERSION",
]

SCHEMA_VERSION = "1.0"


class Side(StrEnum):
    front = "front"
    back = "back"


class Script(StrEnum):
    arabic = "Arab"
    latin = "Latn"
    mixed = "Mixed"
    common = "Zyyy"  # digits / punctuation only
    unknown = "Zzzz"


class Direction(StrEnum):
    rtl = "rtl"
    ltr = "ltr"


class ExtractionMethod(StrEnum):
    ocr = "ocr"  # verbatim OCR text
    rule = "rule"  # deterministic regex / lexicon / validator
    layout = "layout"  # position / block heuristics
    ner = "ner"
    llm = "llm"
    qr = "qr"
    manual = "manual"


class ReviewStatus(StrEnum):
    unreviewed = "unreviewed"
    needs_review = "needs_review"
    verified = "verified"
    corrected = "corrected"
    rejected = "rejected"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BBox(_Model):
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


class OcrLine(_Model):
    """One recognized text line. ``text`` is exactly what the recognizer produced."""

    id: str
    side: Side
    text: str
    normalized_text: str
    bbox: BBox
    polygon: list[list[float]] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1, description="Recognizer score, not calibrated")
    detection_confidence: float | None = Field(default=None, ge=0, le=1)
    script: Script = Script.unknown
    language: str = "und"  # BCP-47 primary tag: ar / fr / en / und
    language_confidence: float | None = None
    direction: Direction = Direction.ltr
    model: str | None = None
    block_index: int | None = None
    line_index: int | None = None  # position in reconstructed reading order
    alternatives: list[dict[str, Any]] = Field(default_factory=list)  # other recognizer hypotheses


class QrCode(_Model):
    id: str
    side: Side
    raw: str
    kind: Literal["url", "vcard", "mecard", "email", "tel", "text", "wifi"] = "text"
    parsed: dict[str, Any] = Field(default_factory=dict)
    url_is_safe: bool | None = None  # http(s) only, no credentials, valid host
    bbox: BBox | None = None
    imported: bool = False  # the user decides; never automatic


class CandidateRegion(_Model):
    """A detected area whose label is a *candidate*, not ground truth."""

    id: str
    side: Side
    label: Literal["address", "logo", "text_block", "qr"]
    bbox: BBox
    confidence: float | None = None
    method: str = "heuristic"
    line_ids: list[str] = Field(default_factory=list)


class QualityReport(_Model):
    width: int
    height: int
    blur_score: float  # variance of Laplacian (higher = sharper)
    brightness: float  # 0-255
    contrast: float  # std of luminance
    is_low_resolution: bool
    is_blurry: bool
    is_dark: bool
    is_low_contrast: bool
    warnings: list[str] = Field(default_factory=list)


class PreprocessingStep(_Model):
    name: str
    applied: bool
    details: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(_Model):
    provider: str
    task: str  # detection | recognition | orientation | extraction | qr
    name: str
    version: str | None = None
    languages: list[str] = Field(default_factory=list)
    device: str | None = None


class OcrPage(_Model):
    side: Side
    width: int
    height: int
    lines: list[OcrLine]
    qr_codes: list[QrCode] = Field(default_factory=list)
    regions: list[CandidateRegion] = Field(default_factory=list)
    quality: QualityReport | None = None
    preprocessing: list[PreprocessingStep] = Field(default_factory=list)
    models: list[ModelInfo] = Field(default_factory=list)
    processing_ms: int = 0
    rotation_applied: int = 0  # degrees, clockwise


class LanguageRegion(_Model):
    language: str
    script: Script
    line_ids: list[str]
    share: float  # fraction of recognized characters


class FieldValue(_Model):
    value: Any = None
    original_value: str | None = None  # the OCR evidence text this value was taken from
    normalized_value: Any = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_region_ids: list[str] = Field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.rule
    review_status: ReviewStatus = ReviewStatus.unreviewed
    notes: str | None = None


class Address(_Model):
    id: str
    original_text: str
    normalized_text: str | None = None
    street: str | None = None
    building: str | None = None
    postal_code: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    role: Literal["business", "unknown"] = "unknown"
    role_confidence: float | None = None
    role_evidence: str | None = None
    confidence: float | None = None
    source_region_ids: list[str] = Field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.layout
    review_status: ReviewStatus = ReviewStatus.unreviewed


class _Extraction(_Model):
    schema_version: str = SCHEMA_VERSION
    language_regions: list[LanguageRegion] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    extractor: str = "rules"
    extractor_version: str = "1"
    generated_at: datetime | None = None


class Phone(_Model):
    type: Literal["phone", "mobile", "fax", "whatsapp", "unknown"] = "unknown"
    type_evidence: str | None = None  # the label seen on the card ("Tél", "Mob", "واتساب" …)
    original: str
    e164: str | None = None  # only when confidently determined
    region: str | None = None  # ISO country the number was parsed against
    # card_address: the country printed in the card's own address (business cards only)
    region_inferred_from: Literal["explicit_prefix", "default_region", "card_address", "none"] = "none"
    is_valid: bool = False
    confidence: float | None = None
    source_region_ids: list[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.unreviewed


class QrFieldCheck(_Model):
    """Comparison of one QR-code value with what OCR read on the card. Never auto-resolved."""

    field: str  # full_name | company | job_title | phones | emails | website
    qr_id: str
    qr_value: str
    ocr_value: str | None = None
    status: Literal["match", "conflict", "qr_only"]


class BusinessCardExtraction(_Extraction):
    full_name: FieldValue = Field(default_factory=FieldValue)
    first_name: FieldValue = Field(default_factory=FieldValue)
    last_name: FieldValue = Field(default_factory=FieldValue)
    arabic_name: FieldValue = Field(default_factory=FieldValue)
    job_title: FieldValue = Field(default_factory=FieldValue)
    company: FieldValue = Field(default_factory=FieldValue)
    department: FieldValue = Field(default_factory=FieldValue)
    industry: FieldValue = Field(default_factory=FieldValue)
    specialty: FieldValue = Field(default_factory=FieldValue)
    phones: list[Phone] = Field(default_factory=list)
    emails: list[FieldValue] = Field(default_factory=list)
    website: FieldValue = Field(default_factory=FieldValue)
    linkedin: FieldValue = Field(default_factory=FieldValue)
    social_profiles: list[FieldValue] = Field(default_factory=list)
    address: Address | None = None
    qualifications: list[FieldValue] = Field(default_factory=list)
    certifications: list[FieldValue] = Field(default_factory=list)
    memberships: list[FieldValue] = Field(default_factory=list)
    qr_codes: list[QrCode] = Field(default_factory=list)
    logo: CandidateRegion | None = None
    # verbatim professional scope line, e.g. "Spécialiste des maladies du foie …"
    professional_description: FieldValue = Field(default_factory=FieldValue)
    qr_checks: list[QrFieldCheck] = Field(default_factory=list)
    review_fields: list[str] = Field(default_factory=list)  # paths whose value needs human review
