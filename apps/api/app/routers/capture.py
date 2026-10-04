"""Phone-as-camera: the PC creates a request for (document, side); the same user's phone
polls for it, photographs the card, uploads through the normal image endpoint and marks it done.
Polling only — works on serverless."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import Principal, get_principal
from app.errors import ApiError
from app.models import CaptureRequest, Document, utcnow

router = APIRouter(prefix="/capture-requests", tags=["capture"])
TTL = timedelta(minutes=10)


class CaptureIn(BaseModel):
    document_id: uuid.UUID
    side: Literal["front", "back"]


class CaptureOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    side: str
    status: str
    route: str = "business-cards"


def _out(r: CaptureRequest) -> CaptureOut:
    return CaptureOut(id=r.id, document_id=r.document_id, side=r.side, status=r.status)


def _mine(db: Session, p: Principal, req_id: uuid.UUID) -> CaptureRequest:
    r = db.get(CaptureRequest, req_id)
    if r is None or r.user_id != p.user.id:
        raise ApiError(404, "capture_not_found", "Capture request not found.")
    return r


@router.post("", response_model=CaptureOut, status_code=201)
def create(body: CaptureIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    doc = db.get(Document, body.document_id)
    if doc is None or doc.workspace_id != p.workspace.id or doc.deleted_at is not None:
        raise ApiError(404, "document_not_found", "Document not found.")
    # one live request per user: a new one replaces the previous
    db.execute(update(CaptureRequest).where(CaptureRequest.user_id == p.user.id, CaptureRequest.status == "pending").values(status="cancelled"))
    r = CaptureRequest(user_id=p.user.id, document_id=doc.id, side=body.side, status="pending")
    db.add(r)
    db.commit()
    return _out(r)


@router.get("/pending", response_model=CaptureOut | None)
def pending(p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    q = (select(CaptureRequest).where(CaptureRequest.user_id == p.user.id, CaptureRequest.status == "pending",
                                      CaptureRequest.created_at >= utcnow() - TTL)
         .order_by(CaptureRequest.created_at.desc()).limit(1))
    r = db.scalars(q).first()
    return _out(r) if r else None


@router.get("/{req_id}", response_model=CaptureOut)
def get(req_id: uuid.UUID, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    return _out(_mine(db, p, req_id))


@router.post("/{req_id}/{action}", response_model=CaptureOut)
def finish(req_id: uuid.UUID, action: Literal["done", "cancel"], p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    r = _mine(db, p, req_id)
    if r.status == "pending":
        r.status = "done" if action == "done" else "cancelled"
        db.commit()
    return _out(r)
