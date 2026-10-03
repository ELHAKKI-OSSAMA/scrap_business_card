from __future__ import annotations

import uuid

import httpx
import hmac

from fastapi import APIRouter, Depends, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import Principal, get_principal
from app.errors import ApiError
from app.models import ProcessingJob
from app.ocr_runtime import provider_status
from app.schemas import JobOut, TranslateIn, TranslateOut
from app.storage import get_storage

router = APIRouter()


@router.get("/health", tags=["system"], summary="Liveness")
def health():
    return {"status": "ok"}


@router.get("/health/ready", tags=["system"], summary="Readiness: database, broker, storage, OCR engine")
def ready(response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    checks: dict[str, dict] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"ok": True}
    except Exception as exc:
        checks["database"] = {"ok": False, "error": type(exc).__name__}
    if s.job_execution == "celery":
        try:
            import redis

            redis.Redis.from_url(s.redis_url or "redis://redis:6379/0", socket_timeout=2).ping()
            checks["broker"] = {"ok": True}
        except Exception as exc:
            checks["broker"] = {"ok": False, "error": type(exc).__name__}
    try:
        checks["storage"] = {"ok": get_storage().healthy(), "backend": s.storage_backend}
    except Exception as exc:
        checks["storage"] = {"ok": False, "error": type(exc).__name__}
    ocr = {p["provider"]: p["available"] for p in provider_status() if p["provider"] != "handwriting"}
    primary = ocr.get(s.ocr_provider, False)
    fallback = ocr.get(s.ocr_fallback_provider, False) if s.ocr_fallback_provider != "none" else False
    # the API process does not run OCR itself in celery mode, but the image is shared with the worker
    checks["ocr"] = {"ok": primary or fallback, "providers": ocr}
    ok = all(c["ok"] for c in checks.values())
    response.status_code = 200 if ok else 503
    return {"status": "ready" if ok else "degraded", "checks": checks}


@router.get("/models", tags=["system"], summary="Installed OCR / extraction models and verified capabilities")
def models(_: Principal = Depends(get_principal)):
    s = get_settings()
    return {
        "ocr": provider_status(),
        "default_provider": s.ocr_provider,
        "fallback_provider": s.ocr_fallback_provider,
        "device": s.ocr_device,
        "extraction": {
            "rules": {"available": True, "version": "1.0", "languages": ["ar", "fr", "en"]},
            "vision_llm": {"available": s.ocr_provider == "ollama" or s.llm_provider == "ollama_vision", "model": s.ollama_model, "external": True},
            "llm": {"available": s.llm_enabled, "provider": s.llm_provider, "model": s.llm_model if s.llm_enabled else None, "external": bool(s.llm_enabled)},
        },
        "translation": {"available": s.translation_provider != "none" and bool(s.translation_url), "provider": s.translation_provider},
        "capabilities": {
            "printed_latin": "verified (synthetic evaluation)",
            "printed_arabic": "verified (synthetic evaluation); digit runs inside Arabic lines are unreliable",
            "handwriting_latin": "not verified",
            "handwriting_arabic": "not supported / not verified",
            "eastern_arabic_digits": "weak (see docs/models/evaluation.md)",
        },
    }


@router.get("/jobs/{job_id}", tags=["jobs"], response_model=JobOut, summary="Processing job status")
def job(job_id: uuid.UUID, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    j = db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id, ProcessingJob.workspace_id == p.workspace.id))
    if j is None:
        raise ApiError(404, "job_not_found", "Job not found.")
    return j


@router.post("/translate", tags=["translation"], response_model=TranslateOut, summary="Optional machine translation (never stored over OCR text)")
def translate(body: TranslateIn, _: Principal = Depends(get_principal)):
    s = get_settings()
    if s.translation_provider == "none" or not s.translation_url:
        raise ApiError(501, "translation_not_configured", "Machine translation is not configured on this server.")
    payload = {"q": body.text, "source": body.source, "target": body.target, "format": "text"}
    if s.translation_api_key:
        payload["api_key"] = s.translation_api_key
    try:
        r = httpx.post(s.translation_url.rstrip("/") + "/translate", json=payload, timeout=30)
        r.raise_for_status()
        out = r.json()["translatedText"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise ApiError(502, "translation_failed", "The translation service failed.") from exc
    return TranslateOut(translated_text=out, provider=s.translation_provider, source=body.source, target=body.target)


@router.get("/usage", tags=["system"], summary="Usage against the plan limits (database, storage, Ollama requests)")
def usage(p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    """Measured from this application's own data; providers do not expose their quotas through an
    API, so the limits are the configured LIMIT_* values (defaults: Supabase Free)."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func

    from app.models import Document, DocumentImage, ProcessingJob

    s = get_settings()
    now = datetime.now(timezone.utc)
    db_bytes = None
    if db.bind.dialect.name == "postgresql":
        db_bytes = db.scalar(text("select pg_database_size(current_database())"))
    storage_bytes = db.scalar(select(func.coalesce(func.sum(DocumentImage.size_bytes), 0))) or 0
    processed_images = db.scalar(select(func.count()).select_from(DocumentImage).where(DocumentImage.processed_key.is_not(None))) or 0
    storage_estimate = int(storage_bytes + processed_images * 250_000)  # processed copies ≈ 250 KB (JPEG ≤1600 px)

    def requests_since(t):
        # one Ollama request per processed side of each cloud job
        q = (select(func.count()).select_from(ProcessingJob)
             .join(DocumentImage, DocumentImage.document_id == ProcessingJob.document_id)
             .where(ProcessingJob.created_at >= t, ProcessingJob.provider == "ollama"))
        return db.scalar(q) or 0

    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month = day.replace(day=1)
    docs = db.scalar(select(func.count()).select_from(Document).where(Document.deleted_at.is_(None))) or 0
    return {
        "measured_at": now.isoformat(),
        "documents": {"active": docs, "workspace": db.scalar(select(func.count()).select_from(Document).where(Document.workspace_id == p.workspace.id, Document.deleted_at.is_(None))) or 0},
        "database": {"used_bytes": db_bytes, "limit_bytes": s.limit_db_mb * 1024 * 1024 if s.limit_db_mb else None},
        "storage": {"used_bytes": storage_estimate, "limit_bytes": s.limit_storage_mb * 1024 * 1024 if s.limit_storage_mb else None, "estimated": True},
        "ollama": {
            "model": s.ollama_model if s.ocr_provider == "ollama" or s.llm_provider == "ollama_vision" else None,
            "keys": len(s.ollama_key_list),
            "requests_today": requests_since(day),
            "requests_month": requests_since(month),
            "requests_7d": requests_since(now - timedelta(days=7)),
            "limit_week": s.limit_ollama_requests_week or None,
            "limit_day": s.limit_ollama_requests_day or None,
            "limit_month": s.limit_ollama_requests_month or None,
        },
        "vercel": {"max_request_mb": 4.5, "function_timeout_s": 60},
        "warn_percent": s.usage_warn_percent,
    }


@router.get("/internal/retention", include_in_schema=False)
def retention_cron(request: Request):
    """Retention purge for serverless deployments (Vercel Cron); replaces the Celery beat job."""
    secret = get_settings().cron_secret
    auth = request.headers.get("authorization", "")
    if not secret or not hmac.compare_digest(auth, f"Bearer {secret}"):
        raise ApiError(404, "not_found", "Not found.")
    from app.services.retention import purge

    return purge()


@router.get("/metrics", include_in_schema=False)
def metrics():
    if not get_settings().metrics_enabled:
        raise ApiError(404, "not_found", "Not found.")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
