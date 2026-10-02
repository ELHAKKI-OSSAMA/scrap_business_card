# Production on Vercel (cloud-only)

One Vercel project serves the web app and the whole API. Nothing runs on your own server.

| Piece | Service | How |
|---|---|---|
| Web app (React SPA) | Vercel static | `vercel.json` → `buildCommand`, `outputDirectory` |
| API (FastAPI) | Vercel Python function `api/index.py` | `/api/*` rewrite, `requirements.txt` |
| OCR + extraction | **Ollama Cloud**, Gemma 4 (`gemma4:31b`) | `OCR_PROVIDER=ollama` |
| Database | PostgreSQL (e.g. Supabase) | `DATABASE_URL`, `DB_SERVERLESS=true` |
| Images | S3-compatible storage (e.g. Supabase Storage) | `STORAGE_BACKEND=s3` |
| Jobs | inside the request | `JOB_EXECUTION=sync` (no Redis / Celery) |
| Retention purge | Vercel Cron, daily 03:00 UTC | `GET /api/v1/internal/retention` + `CRON_SECRET` |

PaddleOCR, OpenCV, Tesseract, Redis and Celery are **not** used in this mode. The function's
dependencies weigh ≈ 204 MB installed (measured in `vercel-sim.Dockerfile`).

## What changes in cloud-only mode (honest limits)

* Each card side is one Gemma 4 request (≈ 3.6 s mean, p95 ≈ 6 s on the synthetic set).
* The model gives **no confidence scores**: line and field `confidence` is `null`. Fields set or
  changed by the model are `needs_review`; values not found in the model's own transcription are
  rejected (`warnings: llm_rejected:…`).
* Line boxes are the model's approximate coordinates (good enough for the review overlay).
* No image preprocessing, no QR decoding, no logo detection.
* Card images and their text are sent to Ollama Cloud: get the client's consent.
* Uploads larger than 2.5 MB are downscaled in the browser (Vercel caps request bodies at 4.5 MB).

## Accuracy (synthetic set, 108 cards — not real-world accuracy)

| | PaddleOCR + rules | PaddleOCR + rules + Gemma | **Ollama only (this mode)** |
|---|---|---|---|
| OCR CER (all / Arabic) | 0.0075 / 0.0726 | same | **0.0001 / 0.0011** |
| company | 0.907 | 0.907 | **1.000** |
| postal code | 0.880 | 0.880 | **1.000** |
| e-mail F1 | 0.907 | 0.907 | **1.000** |
| job_title | 0.972 | 0.972 | 0.991 |
| full_name, phones, website, city | 1.000 | 1.000 | 1.000 |

Reports: `ml/evaluation/reports/synthetic-{paddleocr,paddleocr-vision,ollama}.md`.
Validate on real photographed cards before relying on these numbers.

## 1. Database (Supabase example)

1. Create a project in an EU region.
2. Run the migrations **from your machine** (the function never migrates):
   ```bash
   cd apps/api
   DATABASE_URL="postgresql+psycopg://postgres.<ref>:<password>@<host>:5432/postgres" alembic upgrade head
   ```
3. For Vercel use the **pooler** URL (transaction mode, port 6543) with `DB_SERVERLESS=true`
   (NullPool, no prepared statements).

## 2. Storage (Supabase Storage S3)

Create a **private** bucket and S3 access keys (Storage → S3 connection), then set
`S3_ENDPOINT_URL=https://<ref>.supabase.co/storage/v1/s3`, `S3_REGION=<project region>`,
`S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_FORCE_PATH_STYLE=true`, `S3_SSE=` (empty).

## 3. Vercel project

Import the GitHub repository, root directory = repository root (it reads `vercel.json`).
Environment variables (Production):

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `JWT_SECRET` | long random string (≥ 32 chars) |
| `DATABASE_URL` | pooler URL, `postgresql+psycopg://…:6543/postgres` |
| `S3_*` | see above |
| `OLLAMA_KEYS` | your Ollama API key(s), comma-separated |
| `OLLAMA_MODEL` | `gemma4:31b` |
| `CRON_SECRET` | long random string (Vercel sends it to the cron route) |
| `ALLOW_REGISTRATION` | `false` once the accounts exist |

`api/index.py` already defaults `OCR_PROVIDER=ollama`, `JOB_EXECUTION=sync`,
`STORAGE_BACKEND=s3`, `DB_SERVERLESS=true`.

Plan note: Vercel Hobby is for non-commercial use; a client deployment normally needs Pro.
Ollama Cloud free usage has limits; several keys from different accounts to bypass them may break
Ollama's terms — prefer one paid account.

## 4. Test it locally first (same code path)

```bash
MSYS_NO_PATHCONV=1 VITE_BASE=/ npm run build -w apps/business-card-web
docker compose -f docker-compose.vercel-sim.yml up -d --build      # http://localhost:8090
python tests/business_card/api_suite.py --base http://localhost:8090/api/v1
E2E_CARD_URL=http://localhost:8090 npm run e2e
```

The simulation runs `api/index.py` with `requirements.txt` only, PostgreSQL, an S3 server
(SeaweedFS, path-style, no SSE) and nginx applying the `vercel.json` routes and the 4.5 MB body
limit. Verified on 2026-10-02: readiness OK, `workflows.py` OK, `api_suite.py` 0 failures
(10-card batch 10/10), Playwright E2E passed.
