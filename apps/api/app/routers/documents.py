"""Business-card router (``/business-cards``) generated from a ``ProductSpec``.

Every query is scoped by the caller's workspace: documents of other workspaces are reported
as 404 (not 403) so their existence is not revealed."""

from __future__ import annotations

import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from PIL import Image
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import Principal, audit, client_ip, get_principal, require_editor
from app.errors import ApiError
from app.jobs import dispatch
from app.models import Document, DocumentImage, DocumentKey, ExtractionResult, OcrRegion, ProcessingJob, ReviewEvent
from app.products import ProductSpec
from app.ratelimit import check_rate
from app.scanning import scan_bytes
from app.schemas import (
    BulkIdsIn,
    DocumentCreate,
    DocumentMetaUpdate,
    DocumentOut,
    DocumentSummary,
    DuplicateOut,
    ErrorResponse,
    FieldsPatch,
    ImageOut,
    JobAccepted,
    JobOut,
    MergeIn,
    OcrLineOut,
    OcrPageOut,
    Page,
    ProcessIn,
    RegionOut,
    ReviewEventOut,
    ReviewIn,
)
from app.services.fields import apply_changes
from app.services.processing import build_search_text
from app.storage import get_storage
from document_preprocessing import ImageValidationError, validate_image_bytes
from extraction import dedupe_keys, to_csv, to_json, to_vcard
from language_detection import normalize_search

ERRORS = {401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}
_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/tiff": "tif"}


def _get_doc(db: Session, p: Principal, spec: ProductSpec, doc_id: uuid.UUID, *, include_deleted: bool = False) -> Document:
    q = select(Document).where(Document.id == doc_id, Document.workspace_id == p.workspace.id, Document.product == spec.key)
    if not include_deleted:
        q = q.where(Document.deleted_at.is_(None))
    doc = db.scalar(q)
    if doc is None:
        raise ApiError(404, "document_not_found", "Document not found.")
    return doc


def _image_out(spec: ProductSpec, doc: Document, img: DocumentImage) -> ImageOut:
    base = f"{get_settings().api_prefix}/{spec.route}/{doc.id}/images/{img.side}"
    return ImageOut(
        side=img.side, mime=img.mime, width=img.width, height=img.height, processed_width=img.processed_width, processed_height=img.processed_height,
        size_bytes=img.size_bytes, sha256=img.sha256, url=base + "?variant=original", processed_url=(base + "?variant=processed") if img.processed_key else None,
    )


def _latest_job(db: Session, doc: Document) -> ProcessingJob | None:
    return db.scalar(select(ProcessingJob).where(ProcessingJob.document_id == doc.id).order_by(ProcessingJob.created_at.desc()).limit(1))


def _ocr_pages(db: Session, doc: Document) -> list[OcrPageOut]:
    if doc.latest_run_id is None:
        return []
    rows = db.scalars(select(OcrRegion).where(OcrRegion.document_id == doc.id, OcrRegion.job_id == doc.latest_run_id)).all()
    pages: dict[str, OcrPageOut] = {}
    for r in sorted(rows, key=lambda r: (r.side, r.line_index if r.line_index is not None else 10_000)):
        page = pages.setdefault(r.side, OcrPageOut(side=r.side, width=None, height=None, lines=[], regions=[]))
        if r.kind == "line":
            extra = r.extra or {}
            page.width = extra.get("page_width", page.width)
            page.height = extra.get("page_height", page.height)
            page.lines.append(
                OcrLineOut(id=r.region_key, side=r.side, text=r.text, normalized_text=r.normalized_text, bbox=r.bbox, polygon=r.polygon, confidence=r.confidence, script=r.script,
                           language=r.language, direction=r.direction, model=r.model_name, block_index=r.block_index, line_index=r.line_index, extra=extra)
            )
        else:
            extra = r.extra or {}
            page.regions.append(RegionOut(id=r.region_key, side=r.side, label=r.label, bbox=r.bbox, confidence=r.confidence, method=extra.get("method"), line_ids=extra.get("line_ids", [])))
    for img in doc.images:
        if img.side in pages:
            pages[img.side].width = pages[img.side].width or img.processed_width
            pages[img.side].height = pages[img.side].height or img.processed_height
    return [pages[k] for k in sorted(pages)]


def _doc_out(db: Session, spec: ProductSpec, doc: Document, *, detail: bool = False) -> DocumentOut:
    job = _latest_job(db, doc)
    machine = None
    if detail and doc.latest_run_id:
        er = db.scalar(select(ExtractionResult).where(ExtractionResult.job_id == doc.latest_run_id))
        machine = er.data if er else None
    return DocumentOut(
        id=doc.id, product=doc.product, client_ref=doc.client_ref, title=doc.title, notes=doc.notes, status=doc.status, review_status=doc.review_status, favorite=bool(doc.favorite),
        version=doc.version, languages=doc.languages, data=doc.data, machine_data=machine,
        images=[_image_out(spec, doc, i) for i in sorted(doc.images, key=lambda i: i.side != "front")],
        latest_job=JobOut.model_validate(job) if job else None, ocr=_ocr_pages(db, doc) if detail else None,
        created_at=doc.created_at, updated_at=doc.updated_at, processed_at=doc.processed_at,
    )


def _summary(spec: ProductSpec, doc: Document) -> DocumentSummary:
    return DocumentSummary(
        id=doc.id, product=doc.product, title=doc.title, status=doc.status, review_status=doc.review_status, favorite=bool(doc.favorite), languages=doc.languages,
        summary=spec.summary(doc.data), sides=sorted((i.side for i in doc.images), key=lambda s: s != "front"), created_at=doc.created_at, updated_at=doc.updated_at,
    )


def _refresh_derived(db: Session, spec: ProductSpec, doc: Document) -> None:
    texts = db.scalars(select(OcrRegion.text).where(OcrRegion.document_id == doc.id, OcrRegion.job_id == doc.latest_run_id, OcrRegion.kind == "line")).all() if doc.latest_run_id else []
    doc.search_text = build_search_text(spec.key, doc.data or {}, [t for t in texts if t], doc.title)
    if spec.key == "business_card":
        db.query(DocumentKey).filter(DocumentKey.document_id == doc.id).delete()
        for k in dedupe_keys(doc.data or {}):
            db.add(DocumentKey(document_id=doc.id, key=k[:255], workspace_id=doc.workspace_id))


def make_router(spec: ProductSpec) -> APIRouter:
    r = APIRouter(prefix=f"/{spec.route}", tags=[spec.route], responses=ERRORS)
    label = spec.key.replace("_", " ")

    @r.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED, summary=f"Create a {label}")
    def create(body: DocumentCreate, request: Request, response: Response, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        if body.client_ref:
            existing = db.scalar(select(Document).where(Document.workspace_id == p.workspace.id, Document.client_ref == body.client_ref))
            if existing is not None:
                if existing.product != spec.key:
                    raise ApiError(409, "client_ref_conflict", "client_ref is already used by another product.")
                response.status_code = status.HTTP_200_OK
                return _doc_out(db, spec, existing)
        doc = Document(workspace_id=p.workspace.id, product=spec.key, client_ref=body.client_ref, title=body.title, notes=body.notes, created_by=p.user.id, status="draft")
        db.add(doc)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()  # concurrent replay of the same client_ref
            existing = db.scalar(select(Document).where(Document.workspace_id == p.workspace.id, Document.client_ref == body.client_ref))
            response.status_code = status.HTTP_200_OK
            return _doc_out(db, spec, existing)
        audit(db, f"{spec.key}.create", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request))
        db.commit()
        return _doc_out(db, spec, doc)

    @r.get("", response_model=Page, summary=f"List / search {label}s")
    def list_docs(
        q: str | None = Query(default=None, max_length=200, description="Accent-, case- and Arabic-diacritic-insensitive search"),
        status_: str | None = Query(default=None, alias="status"),
        review_status: str | None = None,
        favorite: bool | None = Query(default=None, description="Only favourites (true) / non-favourites (false)"),
        language: Literal["ar", "fr", "en"] | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort: Literal["updated_desc", "updated_asc", "created_desc", "created_asc"] = "updated_desc",
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        p: Principal = Depends(get_principal),
        db: Session = Depends(get_db),
    ):
        conds = [Document.workspace_id == p.workspace.id, Document.product == spec.key, Document.deleted_at.is_(None)]
        if q:
            for term in normalize_search(q).split()[:8]:
                conds.append(Document.search_text.contains(term, autoescape=True))
        if status_:
            conds.append(Document.status == status_)
        if review_status:
            conds.append(Document.review_status == review_status)
        if favorite is not None:
            conds.append(Document.favorite.is_(favorite))
        if created_from:
            conds.append(Document.created_at >= created_from)
        if created_to:
            conds.append(Document.created_at <= created_to)
        base = select(Document).where(and_(*conds))
        docs_all = None
        if language:
            # JSON containment differs across databases; filter in Python on the scoped set
            docs_all = [d for d in db.scalars(base).all() if language in (d.languages or [])]
        order = {
            "updated_desc": Document.updated_at.desc(), "updated_asc": Document.updated_at.asc(),
            "created_desc": Document.created_at.desc(), "created_asc": Document.created_at.asc(),
        }[sort]
        if docs_all is not None:
            key = (lambda d: d.updated_at) if sort.startswith("updated") else (lambda d: d.created_at)
            docs_all.sort(key=key, reverse=sort.endswith("desc"))
            total = len(docs_all)
            items = docs_all[(page - 1) * page_size : page * page_size]
        else:
            total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
            items = db.scalars(base.order_by(order).offset((page - 1) * page_size).limit(page_size)).all()
        return Page(items=[_summary(spec, d) for d in items], total=total, page=page, page_size=page_size)

    @r.get("/export", summary=f"Bulk export {label}s", response_class=Response)
    def export_many(
        request: Request,
        format: Literal["csv", "json", "vcf"] = "csv",
        q: str | None = Query(default=None, max_length=200),
        ids: str | None = Query(default=None, max_length=20000, description="Comma-separated document ids (selection)"),
        favorite: bool | None = None,
        p: Principal = Depends(get_principal),
        db: Session = Depends(get_db),
    ):
        if format not in spec.export_formats:
            raise ApiError(422, "unsupported_format", f"Format '{format}' is not available for this product.")
        conds = [Document.workspace_id == p.workspace.id, Document.product == spec.key, Document.deleted_at.is_(None)]
        if q:
            for term in normalize_search(q).split()[:8]:
                conds.append(Document.search_text.contains(term, autoescape=True))
        if ids:
            try:
                wanted = [uuid.UUID(x) for x in ids.split(",") if x.strip()][:500]
            except ValueError as exc:
                raise ApiError(422, "invalid_ids", "ids must be comma-separated UUIDs.") from exc
            conds.append(Document.id.in_(wanted))
        if favorite is not None:
            conds.append(Document.favorite.is_(favorite))
        docs = db.scalars(select(Document).where(and_(*conds)).order_by(Document.updated_at.desc()).limit(5000)).all()
        audit(db, f"{spec.key}.export_bulk", user=p.user, workspace_id=p.workspace.id, ip=client_ip(request), format=format, count=len(docs))
        db.commit()
        return _export_response(spec, [_export_dict(d) for d in docs], format, f"{spec.route}-export")

    @r.post("/bulk-delete", summary=f"Delete several {label}s (soft delete)")
    def bulk_delete(body: BulkIdsIn, request: Request, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        docs = db.scalars(select(Document).where(Document.workspace_id == p.workspace.id, Document.product == spec.key,
                                                 Document.deleted_at.is_(None), Document.id.in_(body.ids))).all()
        now = datetime.now(timezone.utc)
        for doc in docs:
            doc.deleted_at = now
            db.query(DocumentKey).filter(DocumentKey.document_id == doc.id).delete()
        audit(db, f"{spec.key}.delete_bulk", user=p.user, workspace_id=p.workspace.id, ip=client_ip(request), count=len(docs))
        db.commit()
        return {"deleted": len(docs)}

    @r.get("/{doc_id}", response_model=DocumentOut, summary=f"Get a {label} with OCR regions")
    def get_doc(doc_id: uuid.UUID, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
        return _doc_out(db, spec, _get_doc(db, p, spec, doc_id), detail=True)

    @r.patch("/{doc_id}", response_model=DocumentOut, summary="Update title / transcription notes")
    def update_meta(doc_id: uuid.UUID, body: DocumentMetaUpdate, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(doc, k, v)
        doc.version += 1
        _refresh_derived(db, spec, doc)
        db.commit()
        return _doc_out(db, spec, doc, detail=True)

    @r.post("/{doc_id}/images", response_model=DocumentOut, summary="Upload the front or back image")
    async def upload(doc_id: uuid.UUID, request: Request, side: Literal["front", "back"] = Query(...), file: UploadFile = File(...), p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        s = get_settings()
        check_rate(f"upload:{p.user.id}", s.rate_limit_upload_per_minute)
        doc = _get_doc(db, p, spec, doc_id)
        limit = s.max_upload_mb * 1024 * 1024
        data = await file.read(limit + 1)
        if len(data) > limit:
            raise ApiError(413, "file_too_large", f"File exceeds the {s.max_upload_mb} MB limit.")
        try:
            v = validate_image_bytes(data, max_bytes=limit, max_pixels=s.max_image_pixels)
        except ImageValidationError as exc:
            raise ApiError(415 if exc.code in ("unsupported_type", "type_mismatch") else 422, exc.code, exc.message) from exc
        scan = scan_bytes(data)
        if not scan.clean:
            audit(db, "upload.malware_rejected", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), signature=scan.signature)
            db.commit()
            raise ApiError(422, "malware_detected", "The file was rejected by the malware scanner.")
        existing = next((i for i in doc.images if i.side == side), None)
        if existing is not None and existing.sha256 == v.sha256:
            return _doc_out(db, spec, doc)  # idempotent re-upload (offline sync retries)
        storage = get_storage()
        key = f"ws/{p.workspace.id}/docs/{doc.id}/original/{side}-{uuid.uuid4().hex}.{_EXT[v.mime]}"
        storage.put(key, data, v.mime)
        if existing is not None:
            for k in (existing.storage_key, existing.processed_key):
                if k:
                    storage.delete(k)
            db.delete(existing)
            db.flush()
        db.add(DocumentImage(document_id=doc.id, side=side, storage_key=key, mime=v.mime, width=v.width, height=v.height, sha256=v.sha256, size_bytes=v.size_bytes))
        doc.status = "ready"
        doc.version += 1
        audit(db, f"{spec.key}.upload", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), side=side, size=v.size_bytes, mime=v.mime)
        db.commit()
        db.refresh(doc)
        return _doc_out(db, spec, doc)

    @r.delete("/{doc_id}/images/{side}", response_model=DocumentOut, summary="Remove one side's image")
    def delete_image(doc_id: uuid.UUID, side: Literal["front", "back"], p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        img = next((i for i in doc.images if i.side == side), None)
        if img is None:
            raise ApiError(404, "image_not_found", "No image for this side.")
        storage = get_storage()
        for k in (img.storage_key, img.processed_key):
            if k:
                storage.delete(k)
        db.delete(img)
        doc.version += 1
        db.commit()
        db.refresh(doc)
        if not doc.images:
            doc.status = "draft"
            db.commit()
        return _doc_out(db, spec, doc)

    @r.get("/{doc_id}/images/{side}", summary="Download an image (original, processed or thumbnail)", response_class=Response)
    def get_image(doc_id: uuid.UUID, side: Literal["front", "back"], variant: Literal["original", "processed", "thumb"] = "original", p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        img = next((i for i in doc.images if i.side == side), None)
        if img is None:
            raise ApiError(404, "image_not_found", "No image for this side.")
        key = img.processed_key if variant == "processed" else img.storage_key
        if key is None:
            raise ApiError(404, "image_not_found", "Image not processed yet.")
        data = get_storage().get(key)
        mime = "image/jpeg" if variant == "processed" else img.mime
        if variant == "thumb":
            im = Image.open(io.BytesIO(data))
            from PIL import ImageOps

            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((360, 360))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=80)
            data, mime = buf.getvalue(), "image/jpeg"
        return Response(content=data, media_type=mime, headers={"Cache-Control": "private, max-age=300", "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"})

    @r.post("/{doc_id}/process", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED, summary="Run OCR + extraction (asynchronous job)")
    def process(doc_id: uuid.UUID, request: Request, response: Response, body: ProcessIn | None = None, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        body = body or ProcessIn()
        doc = _get_doc(db, p, spec, doc_id)
        if not doc.images:
            raise ApiError(409, "no_images", "Upload at least one image before processing.")
        opts = {
            "languages": sorted(body.languages) if body.languages else None,
            "provider": body.provider,
            "use_llm": body.use_llm,
            "default_phone_region": (body.default_phone_region or p.user.default_phone_region or "").upper() or None,
        }
        fingerprint = json.dumps({"product": spec.key, "images": sorted((i.side, i.sha256) for i in doc.images), "opts": opts}, sort_keys=True)
        input_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
        if not body.force:
            prev = db.scalar(select(ProcessingJob).where(ProcessingJob.document_id == doc.id, ProcessingJob.input_hash == input_hash, ProcessingJob.status.in_(("queued", "running", "completed"))).order_by(ProcessingJob.created_at.desc()))
            if prev is not None:
                response.status_code = status.HTTP_200_OK
                return JobAccepted(job_id=prev.id, status=prev.status, document_id=doc.id, reused=True)
        job = ProcessingJob(document_id=doc.id, workspace_id=p.workspace.id, input_hash=input_hash, options=opts, status="queued")
        db.add(job)
        doc.status = "queued"
        audit(db, f"{spec.key}.process", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), provider=body.provider, use_llm=body.use_llm)
        db.commit()
        task_id = dispatch(job.id)
        if task_id:
            job.task_id = task_id
            db.commit()
        db.refresh(job)
        return JobAccepted(job_id=job.id, status=job.status, document_id=doc.id)

    @r.patch("/{doc_id}/fields", response_model=DocumentOut, summary="Correct extracted fields")
    def patch_fields(doc_id: uuid.UUID, body: FieldsPatch, request: Request, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        if doc.data is None:
            raise ApiError(409, "not_processed", "The document has no extracted data yet.")
        if body.expected_version is not None and body.expected_version != doc.version:
            raise ApiError(409, "version_conflict", "The document was modified by someone else. Reload and retry.", {"current_version": doc.version})
        new_data, events = apply_changes(doc.data, body.changes, spec.schema, default_region=p.user.default_phone_region)
        doc.data = new_data
        doc.version += 1
        for e in events:
            db.add(ReviewEvent(document_id=doc.id, user_id=p.user.id, action=e["action"], path=e["path"], old_value=e["old_value"], new_value=e["new_value"]))
        _refresh_derived(db, spec, doc)
        audit(db, f"{spec.key}.fields_changed", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), paths=[c.path for c in body.changes])
        db.commit()
        return _doc_out(db, spec, doc, detail=True)

    @r.post("/{doc_id}/review", response_model=DocumentOut, summary="Set the document review status")
    def review(doc_id: uuid.UUID, body: ReviewIn, request: Request, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        old = doc.review_status
        doc.review_status = body.status
        doc.version += 1
        db.add(ReviewEvent(document_id=doc.id, user_id=p.user.id, action="review", path=None, old_value=old, new_value=body.status, note=body.note))
        audit(db, f"{spec.key}.review", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), status=body.status)
        db.commit()
        return _doc_out(db, spec, doc, detail=True)

    @r.get("/{doc_id}/history", response_model=list[ReviewEventOut], summary="Review / correction history")
    def history(doc_id: uuid.UUID, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        return db.scalars(select(ReviewEvent).where(ReviewEvent.document_id == doc.id).order_by(ReviewEvent.created_at.asc())).all()

    @r.get("/{doc_id}/export", summary=f"Export one {label}", response_class=Response)
    def export_one(doc_id: uuid.UUID, request: Request, format: Literal["json", "csv", "vcf"] = "json", p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
        if format not in spec.export_formats:
            raise ApiError(422, "unsupported_format", f"Format '{format}' is not available for this product.")
        doc = _get_doc(db, p, spec, doc_id)
        audit(db, f"{spec.key}.export", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), format=format)
        db.commit()
        return _export_response(spec, [_export_dict(doc)], format, f"{spec.key}-{doc.id}")

    @r.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary=f"Delete a {label} (soft delete, purged after the retention period)")
    def delete_doc(doc_id: uuid.UUID, request: Request, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
        doc = _get_doc(db, p, spec, doc_id)
        doc.deleted_at = datetime.now(timezone.utc)
        db.query(DocumentKey).filter(DocumentKey.document_id == doc.id).delete()
        audit(db, f"{spec.key}.delete", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request))
        db.commit()
        return Response(status_code=204)

    if spec.key == "business_card":

        @r.get("/{doc_id}/duplicates", response_model=list[DuplicateOut], summary="Suggest possible duplicates (never merged automatically)")
        def duplicates(doc_id: uuid.UUID, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
            doc = _get_doc(db, p, spec, doc_id)
            keys = [k for k in db.scalars(select(DocumentKey.key).where(DocumentKey.document_id == doc.id)).all()]
            if not keys:
                return []
            rows = db.execute(
                select(DocumentKey.document_id, DocumentKey.key).where(DocumentKey.workspace_id == p.workspace.id, DocumentKey.key.in_(keys), DocumentKey.document_id != doc.id)
            ).all()
            matches: dict[uuid.UUID, list[str]] = {}
            for did, k in rows:
                matches.setdefault(did, []).append(k)
            weights = {"email": 0.6, "phone": 0.5, "name": 0.3}
            out = []
            for did, ks in matches.items():
                other = db.scalar(select(Document).where(Document.id == did, Document.deleted_at.is_(None)))
                if other is None:
                    continue
                score = min(1.0, sum(weights[k.split(":")[0]] for k in ks))
                out.append(DuplicateOut(document=_summary(spec, other), matched_keys=sorted(ks), score=round(score, 2)))
            return sorted(out, key=lambda d: -d.score)

        @r.post("/{doc_id}/merge", response_model=DocumentOut, summary="Merge another card into this one (explicit confirmation required)")
        def merge(doc_id: uuid.UUID, body: MergeIn, request: Request, p: Principal = Depends(require_editor), db: Session = Depends(get_db)):
            if not body.confirm:
                raise ApiError(422, "confirmation_required", "Merging requires explicit confirmation.")
            doc = _get_doc(db, p, spec, doc_id)
            other = _get_doc(db, p, spec, body.other_id)
            if other.id == doc.id:
                raise ApiError(422, "invalid_merge", "Cannot merge a document with itself.")
            merged = dict(doc.data or {})
            src = other.data or {}
            filled = []
            for k, v in src.items():
                cur = merged.get(k)
                if isinstance(v, dict) and "value" in v and isinstance(cur, dict) and cur.get("value") in (None, "") and v.get("value") not in (None, ""):
                    merged[k] = v
                    filled.append(k)
                elif isinstance(v, list) and isinstance(cur, list):
                    seen = {_item_key(x) for x in cur}
                    for x in v:
                        if _item_key(x) not in seen:
                            cur.append(x)
                            seen.add(_item_key(x))
                            filled.append(k)
                elif cur is None and v is not None:
                    merged[k] = v
                    filled.append(k)
            doc.data = spec.schema.model_validate(merged).model_dump(mode="json")
            doc.version += 1
            other.deleted_at = datetime.now(timezone.utc)
            db.query(DocumentKey).filter(DocumentKey.document_id == other.id).delete()
            db.add(ReviewEvent(document_id=doc.id, user_id=p.user.id, action="merge", path=None, old_value=None, new_value={"merged_from": str(other.id), "fields": sorted(set(filled))}))
            _refresh_derived(db, spec, doc)
            audit(db, "business_card.merge", user=p.user, workspace_id=p.workspace.id, target_type="document", target_id=str(doc.id), ip=client_ip(request), merged_from=str(other.id))
            db.commit()
            return _doc_out(db, spec, doc, detail=True)

    return r


def _item_key(x) -> str:
    if isinstance(x, dict):
        x = x.get("value") if "value" in x else (x.get("e164") or x.get("original") or x.get("original_text") or x.get("raw"))
    return normalize_search(str(x))


def _export_dict(doc: Document) -> dict:
    return {"id": str(doc.id), "product": doc.product, "title": doc.title, "notes": doc.notes, "review_status": doc.review_status, "languages": doc.languages,
            "created_at": doc.created_at.isoformat() if doc.created_at else None, "updated_at": doc.updated_at.isoformat() if doc.updated_at else None, "data": doc.data}


def _export_response(spec: ProductSpec, docs: list[dict], fmt: str, filename: str) -> Response:
    if fmt == "json":
        body, mime, ext = to_json(docs if len(docs) != 1 else docs[0]), "application/json", "json"
    elif fmt == "csv":
        body, mime, ext = to_csv((spec.csv_row(d) for d in docs), spec.csv_columns), "text/csv; charset=utf-8", "csv"
    else:
        body, mime, ext = "".join(to_vcard(d.get("data") or {}) for d in docs), "text/vcard; charset=utf-8", "vcf"
    return Response(content=body.encode("utf-8"), media_type=mime, headers={"Content-Disposition": f'attachment; filename="{filename}.{ext}"'})
