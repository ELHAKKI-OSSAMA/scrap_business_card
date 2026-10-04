from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import install_error_handlers
from app.observability import RequestContextMiddleware, configure_logging
from app.products import BUSINESS_CARD
from app.routers import auth, capture, system
from app.routers.documents import make_router

DESCRIPTION = """
Backend for **Business Card Intelligence** (Arabic, French and English business cards).

* OCR runs asynchronously: `POST …/process` returns a job id, poll `GET /api/v1/jobs/{job_id}`.
* Every field carries `value`, `original_value` (OCR evidence), `normalized_value`, `confidence`,
  `source_region_ids`, `extraction_method` and `review_status`. Raw OCR text is never overwritten.
* Errors: `{"error": {"code", "message", "details", "request_id"}}`.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if s.ocr_warmup and s.job_execution != "celery":
        from app.ocr_runtime import get_engine

        try:
            warm = getattr(get_engine().provider, "warmup", None)
            if warm:
                warm()
        except Exception as exc:
            logging.getLogger("app").warning("OCR warmup failed: %s", exc)
    yield


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging(s.log_level)
    app = FastAPI(title=s.app_name, version="0.1.0", description=DESCRIPTION, openapi_url=f"{s.api_prefix}/openapi.json", docs_url=f"{s.api_prefix}/docs", redoc_url=f"{s.api_prefix}/redoc", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    if s.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=s.cors_origins, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"], expose_headers=["X-Request-ID", "Content-Disposition"])
    install_error_handlers(app)
    app.include_router(system.router, prefix=s.api_prefix)
    app.include_router(auth.router, prefix=s.api_prefix)
    app.include_router(capture.router, prefix=s.api_prefix)
    app.include_router(make_router(BUSINESS_CARD), prefix=s.api_prefix)
    return app


app = create_app()
