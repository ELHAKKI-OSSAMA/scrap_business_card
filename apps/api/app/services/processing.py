"""Executes one processing job: OCR every side, extract, persist raw OCR + machine extraction."""

from __future__ import annotations

import io
import logging
import time
import uuid
from datetime import datetime, timezone

from PIL import Image
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker
from app.models import Document, DocumentKey, ExtractionResult, OcrRegion, ProcessingJob
from app.observability import JOBS, OCR_DURATION
from app.ocr_runtime import get_engine, vision_client
from app.products import PRODUCTS
from app.storage import get_storage
from document_preprocessing import ImageValidationError, validate_image_bytes
from extraction import OpenAICompatibleClient, dedupe_keys, llm_enrich, merge_vision, vision_enrich
from extraction.vision_llm import AllKeysFailedError
from extraction.common import all_lines
from language_detection import normalize_search
from ocr_core import OcrUnavailableError
from shared_types import OcrPage, Side

log = logging.getLogger("app.processing")


def _jpeg(rgb) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def build_search_text(product_key: str, data: dict, ocr_texts: list[str], title: str | None) -> str:
    spec = PRODUCTS[product_key]
    parts = [title or ""] + spec.search_fields(data) + list(ocr_texts)
    return normalize_search(" ".join(p for p in parts if p))[:20000]


def run_job(job_id: uuid.UUID, db: Session | None = None) -> None:
    own = db is None
    db = db or get_sessionmaker()()
    try:
        _run(db, job_id)
    except Exception:  # noqa: BLE001 – never leave a job "running" (sync mode answers inside the request)
        log.exception("processing error", extra={"job_id": str(job_id)})
        db.rollback()
        job = db.get(ProcessingJob, job_id)
        doc = db.get(Document, job.document_id) if job else None
        if job is not None and doc is not None and job.status in ("queued", "running"):
            _fail(db, job, doc, "processing_error", "unexpected error")
    finally:
        if own:
            db.close()


def _fail(db: Session, job: ProcessingJob, doc: Document, code: str, message: str) -> None:
    job.status = "failed"
    job.error_code = code
    job.error_message = message[:500]
    job.finished_at = datetime.now(timezone.utc)
    doc.status = "failed"
    db.commit()
    JOBS.labels(doc.product, "failed").inc()
    log.warning("job failed", extra={"job_id": str(job.id), "document_id": str(doc.id), "error_code": code})


def _run(db: Session, job_id: uuid.UUID) -> None:
    job = db.get(ProcessingJob, job_id)
    if job is None or job.status not in ("queued", "running"):
        return
    doc = db.get(Document, job.document_id)
    if doc is None or doc.deleted_at is not None:
        job.status = "failed"
        job.error_code = "document_deleted"
        db.commit()
        return
    spec = PRODUCTS[doc.product]
    opts = job.options or {}
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    doc.status = "processing"
    db.commit()
    t0 = time.perf_counter()
    storage = get_storage()
    settings = get_settings()
    try:
        engine = get_engine(opts.get("provider"))
    except OcrUnavailableError as exc:
        _fail(db, job, doc, "ocr_engine_unavailable", str(exc))
        return

    pages: list[OcrPage] = []
    images = {}
    raw_images: list[bytes] = []
    try:
        for img in sorted(doc.images, key=lambda i: i.side):
            raw = storage.get(img.storage_key)
            v = validate_image_bytes(raw, max_bytes=settings.max_upload_mb * 1024 * 1024, max_pixels=settings.max_image_pixels)
            page, processed = engine.process_page(v.rgb, Side(img.side), languages=opts.get("languages"), exif_transposed=v.exif_transposed)
            key = f"ws/{doc.workspace_id}/docs/{doc.id}/processed/{img.side}-{job.id}.jpg"
            storage.put(key, _jpeg(processed), "image/jpeg")
            old_key = img.processed_key
            img.processed_key = key
            img.processed_width, img.processed_height = page.width, page.height
            if old_key and old_key != key:
                storage.delete(old_key)
            pages.append(page)
            images[Side(img.side)] = processed
            raw_images.append(_jpeg(processed))
    except (OcrUnavailableError, AllKeysFailedError) as exc:
        _fail(db, job, doc, "ocr_engine_unavailable", str(exc))
        return
    except ImageValidationError as exc:
        _fail(db, job, doc, exc.code, exc.message)
        return
    except ValueError as exc:  # cloud mode: the model answer was not valid JSON for the schema
        _fail(db, job, doc, "ocr_invalid_answer", type(exc).__name__)
        return
    except Exception as exc:  # noqa: BLE001 – recorded on the job, re-raised to logs only
        log.exception("processing error", extra={"job_id": str(job.id)})
        _fail(db, job, doc, "processing_error", type(exc).__name__)
        return

    default_region = opts.get("default_phone_region") or settings.default_phone_region
    extraction, regions = spec.extract(pages, images, {"default_phone_region": default_region})
    cards = getattr(engine, "cards", None)
    if cards:  # cloud mode: the fields came with the OCR answer
        lines = all_lines(pages)
        for card in cards.values():
            extraction = merge_vision(extraction, card, lines, model=engine.provider.model, default_region=default_region)
    elif settings.llm_provider == "ollama_vision":
        client = vision_client()
        extraction = vision_enrich(extraction, raw_images, all_lines(pages), client, default_region=default_region)
    elif opts.get("use_llm") and settings.llm_enabled:
        client = OpenAICompatibleClient(base_url=settings.llm_base_url or "", model=settings.llm_model or "", api_key=settings.llm_api_key, timeout=settings.llm_timeout_s)
        extraction = llm_enrich(extraction, all_lines(pages), client, settings={"temperature": 0.0})
    elif opts.get("use_llm"):
        extraction.warnings.append("llm_requested_but_not_configured")
    data = spec.schema.model_validate(extraction.model_dump()).model_dump(mode="json")

    # persist raw OCR (immutable per job)
    for page in pages:
        for l in page.lines:
            db.add(
                OcrRegion(
                    document_id=doc.id, job_id=job.id, region_key=l.id, kind="line", side=l.side.value, text=l.text, normalized_text=l.normalized_text,
                    bbox=l.bbox.model_dump(), polygon=l.polygon, confidence=l.confidence, script=l.script.value, language=l.language,
                    direction=l.direction.value, model_name=l.model, block_index=l.block_index, line_index=l.line_index,
                    extra={"detection_confidence": l.detection_confidence, "language_confidence": l.language_confidence, "alternatives": l.alternatives, "page_width": page.width, "page_height": page.height},
                )
            )
    for r in regions:
        db.add(OcrRegion(document_id=doc.id, job_id=job.id, region_key=r.id, kind="candidate", side=r.side.value, label=r.label, bbox=r.bbox.model_dump(), confidence=r.confidence, extra={"method": r.method, "line_ids": r.line_ids}))
    db.add(ExtractionResult(document_id=doc.id, job_id=job.id, schema_version=data.get("schema_version", "1.0"), extractor=data.get("extractor", "rules"), data=data))

    doc.data = data
    doc.languages = data.get("languages") or []
    doc.search_text = build_search_text(doc.product, data, [l.text for p in pages for l in p.lines], doc.title)
    doc.status = "completed"
    doc.review_status = "needs_review" if _needs_review(data) else "unreviewed"
    doc.processed_at = datetime.now(timezone.utc)
    doc.latest_run_id = job.id
    doc.version += 1
    if doc.product == "business_card":
        db.execute(delete(DocumentKey).where(DocumentKey.document_id == doc.id))
        for k in dedupe_keys(data):
            db.add(DocumentKey(document_id=doc.id, key=k[:255], workspace_id=doc.workspace_id))

    elapsed = time.perf_counter() - t0
    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    job.processing_ms = int(elapsed * 1000)
    job.provider = engine.provider.name
    job.model_metadata = [m.model_dump() for m in pages[0].models] if pages else [m.model_dump() for m in engine.provider.models()]
    job.preprocessing = {p.side.value: {"steps": [s.model_dump() for s in p.preprocessing], "rotation_applied": p.rotation_applied, "ocr_ms": p.processing_ms} for p in pages}
    job.quality = {p.side.value: p.quality.model_dump() if p.quality else None for p in pages}
    db.commit()
    OCR_DURATION.labels(doc.product, engine.provider.name).observe(elapsed)
    JOBS.labels(doc.product, "completed").inc()
    log.info("job completed", extra={"job_id": str(job.id), "document_id": str(doc.id), "product": doc.product, "duration_ms": job.processing_ms})


def _needs_review(data: dict) -> bool:
    def walk(o):
        if isinstance(o, dict):
            if o.get("review_status") == "needs_review":
                return True
            return any(walk(v) for v in o.values())
        if isinstance(o, list):
            return any(walk(v) for v in o)
        return False

    return walk(data)

