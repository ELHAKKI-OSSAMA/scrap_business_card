"""Job dispatch. ``JOB_EXECUTION``:
* ``celery`` – enqueue on Redis; a worker container runs it (Docker default)
* ``thread`` – run in a background thread of the API process (single-process development)
* ``sync``   – run inside the request (tests)
"""

from __future__ import annotations

import threading
import uuid

from app.config import get_settings


def dispatch(job_id: uuid.UUID) -> str | None:
    mode = get_settings().job_execution
    if mode == "celery":
        from app.worker import process_document

        res = process_document.delay(str(job_id))
        return res.id
    from app.services.processing import run_job

    if mode == "sync":
        run_job(job_id)
        return None
    threading.Thread(target=run_job, args=(job_id,), daemon=True, name=f"job-{job_id}").start()
    return None
