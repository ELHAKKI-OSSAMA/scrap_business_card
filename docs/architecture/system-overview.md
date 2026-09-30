# System overview

**Business Card Intelligence** reads Arabic, French and English business cards. It is built from
one backend (API + OCR worker), one OCR core library, one web app and one mobile app.
Design decisions and their rationale are recorded in [decisions.md](decisions.md) (D1–D19).

```
 Browser ──► nginx gateway :8080 ──► /cards/      business-card-web (React SPA, static)
 Flutter app ─┘        │           │
                       │           └─ /api/v1/*    api (FastAPI, uvicorn)
                       │                              │  enqueue job (Redis)
                       │                              ▼
                       │                           worker (Celery, queue "ocr")
                       │                              │ OcrEngine → extraction → validation
                       ▼                              ▼
                 postgres 16  ◄──────── documents, OCR lines, fields, jobs, audit
                 local volume / S3 (MinIO) ◄── original + processed images, thumbnails
```

## Components

| Component | Path | Role |
|---|---|---|
| Core library `ocr-suite-core` | `packages/` | Pure-Python: preprocessing, OCR providers, reading order, language detection, extraction, validation. No web/DB dependencies; used by API, worker and the evaluation harness. |
| Shared types | `packages/shared-types` | Pydantic models (Python) mirrored in TypeScript (`ts/index.ts`). |
| API | `apps/api` | FastAPI app, SQLAlchemy 2 models, Alembic migrations, auth, storage, jobs. |
| Worker | same image as API | Celery worker running `run_job` (OCR + extraction). `beat` runs retention purges. |
| Web app | `apps/business-card-web` | Vite + React + TS + Tailwind v4, i18next (en/fr/ar, RTL). Built on `packages/ui`. |
| Mobile | `apps/mobile` | Flutter app: capture, offline drafts, idempotent sync, review. |
| Evaluation | `ml/` | Synthetic data generator and evaluator (CER/WER, detection, fields, entities, calibration, latency). |
| Infrastructure | `infrastructure/`, `docker-compose*.yml` | Dockerfiles, nginx, Prometheus/Grafana, model download. |

## Product definition

`apps/api/app/products.py` defines the business-card `ProductSpec` (route, sides, export formats,
extractor, search fields). `routers/documents.py::make_router(spec)` builds the
`/api/v1/business-cards/*` router, including `duplicates` and `merge`.

## Data model (tables)

`users, workspaces, memberships, refresh_tokens, documents, document_images, processing_jobs,
ocr_regions, extraction_results, review_events, document_keys, audit_events` — migration
`apps/api/alembic/versions/0001_initial_schema.py`.

* Raw OCR (`ocr_regions`, machine extraction) is written once per job and never edited;
  user corrections are stored as the current `data` plus `review_events` history.
* Every row is scoped to a workspace; cross-workspace access returns **404** (not 403) to avoid
  existence leaks.

## Processing flow

1. `POST /business-cards` creates a document (idempotent on `client_ref`).
2. `POST /business-cards/{id}/images?side=front|back` validates the file (type sniffing, size, pixel
   bomb, EXIF orientation), stores the original and a thumbnail. Re-uploading the same bytes is a no-op (sha256).
3. `POST /business-cards/{id}/process` creates a job (idempotent on an input hash) → Celery.
4. Worker: preprocessing → OCR → reading order → language detection → product extraction →
   validation → confidence → persisted. See [ocr-pipeline.md](ocr-pipeline.md).
5. Clients poll `GET /jobs/{id}`, then `GET /business-cards/{id}` for lines, regions and fields.
6. Review: `PATCH /business-cards/{id}/fields` (set/verify/append/remove with optimistic
   `expected_version`), history at `/history`, export at `/export?format=json|csv|vcf`.

Job execution mode is configurable: `celery` (Docker), `thread` (single-process dev),
`sync` (tests).

## Verified in this repository

* Full Docker stack (`docker compose up`) — all services healthy, migration `0001` applied,
  readiness reports database, broker, storage, PaddleOCR and Tesseract OK.
* Playwright E2E through the gateway and HTTP workflow checks
  (`tests/integration/workflows.py`) with real PaddleOCR inference.

Not verified: GPU worker override, MinIO/S3 backend, ClamAV scanning, TLS production override,
monitoring profile. See [../deployment/docker.md](../deployment/docker.md).
