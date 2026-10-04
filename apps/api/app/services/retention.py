"""Retention: hard-delete soft-deleted documents after ``DELETED_RETENTION_DAYS``, drafts never
processed after ``DRAFT_RETENTION_HOURS`` and, if ``DOCUMENT_RETENTION_DAYS`` > 0, any document
older than that. Storage objects are removed too.

Run manually: ``python -m app.cli purge``."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker
from app.models import Document
from app.storage import get_storage


def hard_delete(db: Session, doc: Document) -> None:
    """Remove a document for good: its rows (cascade) and every stored image variant."""
    storage = get_storage()
    for img in doc.images:
        for key in (img.storage_key, img.processed_key):
            if key:
                storage.delete(key)
    db.delete(doc)


def purge(now: datetime | None = None) -> dict:
    s = get_settings()
    now = now or datetime.now(timezone.utc)
    conds = [Document.deleted_at < now - timedelta(days=s.deleted_retention_days)]
    if s.document_retention_days > 0:
        conds.append(Document.created_at < now - timedelta(days=s.document_retention_days))
    if s.draft_retention_hours > 0:
        # images added on the New page but OCR never launched (abandoned)
        conds.append(and_(Document.status.in_(("draft", "ready")), Document.updated_at < now - timedelta(hours=s.draft_retention_hours)))
    removed = 0
    with get_sessionmaker()() as db:
        for doc in db.scalars(select(Document).where(or_(*conds))).all():
            hard_delete(db, doc)
            removed += 1
        db.commit()
    return {"purged": removed}
