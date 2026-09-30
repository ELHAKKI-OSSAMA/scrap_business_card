"""Celery worker: ``celery -A app.worker worker -Q ocr --concurrency 1``.

Concurrency 1 per container keeps a single copy of the OCR models in memory; scale with
more worker replicas. A beat schedule runs the retention purge daily."""

from __future__ import annotations

import logging
import uuid

from celery import Celery
from celery.signals import worker_process_init

from app.config import get_settings
from app.observability import configure_logging

settings = get_settings()
celery_app = Celery("ocr_suite", broker=settings.redis_url or "redis://redis:6379/0", backend=None)
celery_app.conf.update(
    task_default_queue="ocr",
    task_acks_late=True,  # a crashed worker's job is redelivered
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={"retention-purge": {"task": "app.worker.purge_retention", "schedule": 24 * 3600.0}},
)


@worker_process_init.connect
def _init(**_):
    configure_logging(settings.log_level)
    if settings.ocr_warmup:
        from app.ocr_runtime import get_engine

        try:
            eng = get_engine()
            warm = getattr(eng.provider, "warmup", None)
            if warm:
                warm()
        except Exception as exc:  # the job will report the precise error
            logging.getLogger("app.worker").warning("OCR warmup failed: %s", exc)


@celery_app.task(name="app.worker.process_document", bind=True, max_retries=0)
def process_document(self, job_id: str) -> None:
    from app.services.processing import run_job

    run_job(uuid.UUID(job_id))


@celery_app.task(name="app.worker.purge_retention")
def purge_retention() -> dict:
    from app.services.retention import purge

    return purge()
