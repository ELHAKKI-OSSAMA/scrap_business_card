# Business Card Intelligence

Business-card OCR for **Arabic, French and English** cards, including mixed-language and
right-to-left text: contact and professional fields, validated phones and e-mails, QR codes,
duplicate suggestions, vCard / CSV / JSON export.

Everything runs locally (PaddleOCR PP-OCRv5 by default, Tesseract as fallback). No external API
is required. Results are reviewable: every value has a confidence, a link to its source text,
and a correction history; raw OCR output is never modified.

> Accuracy figures in this repository come from **synthetic** data only. Handwritten notes are
> **not** a verified feature.

## Windows: one-click start

* `start-docker.bat` — full stack with Docker (creates `.env` with random secrets if missing),
  then opens http://localhost:8080/cards/.
* `start-local.bat` — without Docker: API on :8000 (SQLite, OCR in a thread, no PostgreSQL/Redis),
  web app on http://localhost:5174/. Needs Python 3.12 + uv and Node.js 20+; installs dependencies
  on first run. Close the two windows to stop.

## Production: Vercel + PostgreSQL + S3 + Ollama Cloud

`vercel.json` + `api/index.py` deploy the web app and the API as one Vercel project. OCR and
extraction run on Gemma 4 via Ollama Cloud (`OCR_PROVIDER=ollama`), data in PostgreSQL (e.g.
Supabase), images in S3-compatible storage (e.g. Supabase Storage). No PaddleOCR, Redis or Celery
in that mode. Guide, limits and measured accuracy: [docs/deployment/vercel.md](docs/deployment/vercel.md).
Local rehearsal: `docker compose -f docker-compose.vercel-sim.yml up -d --build` → http://localhost:8090.

## Quick start (Docker)

```bash
cp .env.example .env            # set JWT_SECRET (≥32 chars) and POSTGRES_PASSWORD
docker compose up -d --build
```

* Business cards: http://localhost:8080/cards/
* API docs: http://localhost:8080/api/v1/docs · readiness: http://localhost:8080/api/v1/health/ready

Register an account on either app (registration is open in development). Details, overrides
(dev, GPU, prod, MinIO, ClamAV, monitoring) and their test status: [docs/deployment/docker.md](docs/deployment/docker.md).

## Local development (without Docker for the apps)

Requirements: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node ≥ 20, Flutter (tested with 3.47.1) with the
Android SDK, Postgres 16 and Redis 7 (or `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis`).

```bash
# Python: core library + API (+ PaddleOCR)
uv venv --python 3.12 .venv
uv pip install -e "./packages[paddle,tesseract,synthetic]" -e ./apps/api
python infrastructure/scripts/download_models.py          # once; caches weights

# API (thread job mode = no Celery needed)
cd apps/api && JOB_EXECUTION=thread alembic upgrade head && JOB_EXECUTION=thread uvicorn app.main:app --port 8000

# Web app (proxy /api → :8000)
npm install
npm run dev:card          # http://localhost:5174/cards/
```

The API reads its settings from environment variables (see `apps/api/app/config.py` and `.env.example`):
at least `DATABASE_URL`, `JWT_SECRET`, `REDIS_URL`.

### Mobile (Flutter)

```bash
cd apps/mobile
flutter pub get
flutter run --dart-define=API_BASE=http://10.0.2.2:8080/api/v1      # Android emulator → Docker gateway
flutter build apk --dart-define=API_BASE=https://<your-app>.vercel.app/api/v1   # production (Vercel)
flutter build apk --debug
```

`10.0.2.2` is the host machine seen from the Android emulator; use the machine's LAN IP for a
physical device. The server URL can also be changed in the app's Settings.

If the Gradle build fails on Windows with `Unable to establish loopback connection`, set
`JAVA_TOOL_OPTIONS=-Djdk.net.unixdomain.tmpdir=C:\jdktmp` (an existing short path) for the build.

## Tests

```bash
pytest                                        # core library: OCR, extraction, validation (real PaddleOCR)
pytest apps/api/tests                         # API (SQLite, sync jobs, recorded OCR)
npm test                                      # web unit tests (ui, business-card-web)
npm run typecheck
cd apps/mobile && flutter analyze && flutter test
# against a running stack:
E2E_CARD_URL=http://localhost:8080/cards npm run e2e
python tests/integration/workflows.py --base http://localhost:8080/api/v1
```

## Evaluation

```bash
python ml/datasets/synthetic/generate.py
python ml/evaluation/evaluate.py --provider paddleocr
```

Results and the PaddleOCR vs Tesseract comparison: [docs/models/evaluation.md](docs/models/evaluation.md).

## Repository layout

```
apps/api                    FastAPI + SQLAlchemy + Alembic + Celery worker
apps/business-card-web      React/TS/Vite/Tailwind — Business Card Intelligence
apps/mobile                 Flutter app (capture, offline drafts, sync, review)
packages/                   ocr-suite-core (Python) + ui (React kit) + shared types
  ocr-core  document-preprocessing  language-detection  extraction  validation  shared-types  ui
ml/                         synthetic dataset generator, evaluation, reports
infrastructure/             Dockerfiles, nginx, monitoring, scripts
tests/                      core tests, Playwright E2E, HTTP integration workflows
docs/                       architecture, models, API, deployment, security, user guides
```

## Documentation

* Architecture: [system overview](docs/architecture/system-overview.md) · [OCR pipeline](docs/architecture/ocr-pipeline.md) · [decisions](docs/architecture/decisions.md)
* Models: [selection](docs/models/model-selection.md) · [evaluation](docs/models/evaluation.md)
* API: [overview](docs/api/openapi.md) · [openapi.json](docs/api/openapi.json)
* Deployment: [Vercel (cloud-only)](docs/deployment/vercel.md) · [Docker](docs/deployment/docker.md) · [production](docs/deployment/production.md)
* [Security and privacy](docs/security/privacy.md)
* [User guide](docs/user-guides/business-card.md) · [Business-card audit](docs/business-card/audit.md)

## Status and limitations

* Verified: CPU Docker stack, business cards end to end with real PaddleOCR, web UI in
  en/fr/ar (RTL), Flutter analyze/tests/debug APK.
* Not tested: GPU worker, production TLS override, S3/MinIO, ClamAV, monitoring profile, the
  mobile app on a device/emulator against a live server, optional LLM/translation providers.
* Known OCR weaknesses: digits inside Arabic lines, Eastern Arabic-Indic digits, handwritten notes.
* Accuracy is measured on synthetic data only; a licensed real-world dataset is needed.
