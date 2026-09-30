"""Structured JSON logging (no request bodies, no OCR text, no images, no tokens) and
Prometheus metrics."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "route"])
OCR_DURATION = Histogram("ocr_processing_seconds", "OCR+extraction time per document", ["product", "provider"], buckets=(0.5, 1, 2, 5, 10, 20, 40, 80, 160))
JOBS = Counter("ocr_jobs_total", "Processing jobs by final status", ["product", "status"])

_SAFE_EXTRA = {"request_id", "method", "route", "status", "duration_ms", "job_id", "document_id", "product", "error_code", "user_id"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"ts": round(record.created, 3), "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        for k in _SAFE_EXTRA:
            if hasattr(record, k):
                out[k] = getattr(record, k)
        if record.exc_info:
            out["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            out["exc"] = self.formatException(record.exc_info)[-2000:]
        return json.dumps(out, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]
    root.setLevel(level)
    # third-party loggers that may echo payloads
    for noisy in ("httpx", "botocore", "urllib3", "ppocr", "paddlex", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id")
        rid = rid if rid and len(rid) <= 64 and rid.replace("-", "").isalnum() else uuid.uuid4().hex
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        dur = time.perf_counter() - t0
        HTTP_REQUESTS.labels(request.method, route_path, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method, route_path).observe(dur)
        response.headers["X-Request-ID"] = rid
        # defence-in-depth headers for API responses
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        logging.getLogger("app.access").info(
            "request", extra={"request_id": rid, "method": request.method, "route": route_path, "status": response.status_code, "duration_ms": int(dur * 1000)}
        )
        return response
