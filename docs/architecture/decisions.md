# Architecture Decision Record (Phase 0)

Date: 2026-09-30. Status: accepted, revised as implementation proceeds.

## 0. Workspace inspection

- The workspace (`Prof Rafiq project/`) was **empty**: no existing code, so there was nothing to preserve or migrate.
- Host toolchain found: Windows 11, Python 3.11/3.14 system, Python 3.12.11 via `uv`, Node 24 / npm 11,
  Flutter 3.47.1 (Dart 3.13) with Android SDK 36, Docker Desktop 29 with Compose v2, NVIDIA RTX 4060 8 GB.
- No iOS toolchain (Windows host), so iOS builds can only be configured and documented here, not built.
- Tesseract is not installed on the host. It is installed inside the Docker image.

## 1. Key decisions

| # | Decision | Reason |
|---|----------|--------|
| D1 | One monorepo for the business-card product: one API, one worker, one OCR engine, one web app and one mobile module | Clear ownership; the OCR core stays a reusable library. |
| D2 | Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7, Celery 5 | This is the stack the spec asks for, and it is mature and well documented. |
| D3 | The core Python packages (`ocr_core`, `language_detection`, `document_preprocessing`, `extraction`, `validation`, `shared_types`) live under `packages/` and are installed as one Python distribution, `ocr-suite-core` | Both the API and the worker import them. A single distribution avoids six `pyproject` files that would each need versioning. |
| D4 | OCR: **PaddleOCR 3.x** is the primary engine (PP-OCRv5 detection; recognition models chosen per script). **Tesseract 5** is a second provider (`ara`, `fra`, `eng` traineddata). Providers sit behind a `OcrProvider` protocol and a registry. | PaddleOCR (Apache-2.0) has the best documented printed Latin/Arabic accuracy among self-hostable engines. Tesseract (Apache-2.0) is a light fallback and a baseline to compare against. |
| D5 | **Per-region recognizer selection.** Text lines are detected once, then each line crop goes to the Latin and/or Arabic recognizer. We keep the hypothesis that is script-consistent and has the higher score. The user can restrict the candidate scripts. | A card is not one language. Choosing a single language per document would break mixed Arabic/French cards. |
| D6 | Language/script ID: Unicode-block script detection (deterministic) plus a small French/English classifier (stop-words and diacritics) that returns `und` when the evidence is weak | Business-card lines are too short for statistical language ID. We return "unknown" rather than guess. |
| D7 | Extraction: staged and deterministic by default (regex + `phonenumbers` + `email-validator` + layout heuristics + keyword lexicons in AR/FR/EN). An **optional** LLM extractor runs only when `LLM_PROVIDER` is configured. Its output is validated with Pydantic and **grounded**: a value that cannot be found in the OCR text is rejected. | The spec says no external calls by default and no fabrication. Deterministic parsers work better than LLMs for emails, URLs and phones. |
| D8 | Every extracted field is a `FieldValue{value, original_value, normalized_value, confidence, source_region_ids, extraction_method, review_status}`. The raw OCR output is stored immutably in `ocr_regions` and is never overwritten. | This keeps three things separate: text the OCR read, values inferred by extraction, and user corrections. |
| D9 | Confidence: OCR confidence is the recognizer score (not calibrated). Extraction confidence is a documented heuristic product (see `docs/models/evaluation.md`). It is `null` when there is no meaningful estimate. | We don't show made-up precision. Calibration needs labelled real data, which we don't have yet. |
| D11 | QR decoding: OpenCV `QRCodeDetector` (it comes with opencv, so there are no native zbar dependencies) | Fewer system dependencies, and it works in the CPU image. |
| D12 | Auth: email + password (Argon2id), short-lived JWT access token, rotating opaque refresh tokens (stored hashed, reuse detection revokes the token family). Each user owns a personal workspace, and every document query is scoped by `workspace_id`. | This meets the spec (hashing, rotation, isolation). Bearer tokens in the `Authorization` header mean browser CSRF does not apply (see privacy.md). |
| D13 | Storage: a `StorageBackend` abstraction with `LocalStorage` (dev) and `S3Storage` (boto3; MinIO in the compose `minio` profile) | Images are stored as object keys, not DB blobs. |
| D14 | Jobs: Celery with a Redis broker. `CELERY_TASK_ALWAYS_EAGER=true` in tests and single-process dev. | Heavy OCR runs asynchronously. Clients poll `GET /jobs/{id}`. |
| D15 | Web: Vite + React 18 + TypeScript + Tailwind v4 app (`business-card-web`) on `packages/ui` (components, i18n, API client, RTL). npm workspaces. | Reusable design system and API client. |
| D16 | i18n: `i18next` JSON catalogues for en/fr/ar. `dir` is set on `<html>` and layout uses logical CSS properties, so it mirrors correctly in RTL. | This meets the RTL and translation requirements. |
| D17 | Mobile: one Flutter app with two modules. `image_picker` handles camera and gallery, `image_cropper` handles manual crop and rotate, and `cunning_document_scanner` does native edge detection and perspective correction (ML Kit on Android, VisionKit on iOS). The server also runs boundary detection and perspective correction. Drafts are stored as JSON and images in app-private storage, and tokens in `flutter_secure_storage`. | There is no on-device OCR, so we never claim offline OCR. |
| D18 | Idempotent sync: the client creates each document with a `client_ref` UUID. The server enforces `UNIQUE(workspace_id, client_ref)` and returns the existing record on replay. Uploading an image replaces that side. Processing an unchanged image set returns the existing job. | Reconnect or retry cannot create duplicates. |
| D19 | Docker Compose profiles: default (cpu), `gpu`, `minio`, `monitoring`, `dev` | CPU is always sufficient to run the stack. GPU is opt-in. |

## 2. Model licensing and language-coverage risks

| Risk | Mitigation |
|------|------------|
| PaddleOCR's `lang` codes map to **different recognition models** depending on the version. For example, French uses the Latin model, and in older versions Arabic uses the PP-OCRv3 Arabic model. | We pin `paddleocr` and name the recognition model explicitly (`model_name=`). We verified which models exist in the installed version (see model-selection.md). |
| No verified **Arabic handwriting** recognizer is available. PaddleOCR and Tesseract are trained mostly on printed text. | Handwriting is marked **not verified**; handwritten notes on cards are read best-effort. A slot for a handwriting provider exists in the registry. |
| Persian and Urdu glyphs (ی ک) can come out of the Arabic recognizer instead of Arabic ي ك | The original text is preserved. A *normalized* field maps Persian code points to Arabic, and a warning is attached. |
| Model weights are downloaded from the Paddle/HuggingFace hosts on first use | The Docker build pre-fetches the weights into the image (`infrastructure/scripts/download_models.py`). An offline deployment copies the model cache volume. |
| Dataset licensing | No third-party datasets are downloaded. Evaluation uses **synthetic** rendered samples, which are clearly marked, plus an annotation format for real images the user supplies. |
| Fonts for synthetic data | Only fonts installed on the host OS or OFL-licensed Noto fonts are used. Generated images are not redistributed as real data. |

## 3. Milestones

1. Foundation: schemas, DB and migrations, auth, storage, jobs, OCR interface, health.
2. OCR engine: Paddle and Tesseract adapters, preprocessing, script ID, evaluation scripts.
4. Business card product: API, extraction, validation, QR, dedupe, vCard, web app.
5. Mobile: Flutter modules, offline drafts, sync, i18n, Android build.
6. Docker and ops: compose profiles, nginx, health checks, monitoring, docs.
7. End-to-end validation and final report.
