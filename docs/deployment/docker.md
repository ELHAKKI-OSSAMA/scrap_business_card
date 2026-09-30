# Docker deployment

## Default CPU stack (verified)

```bash
cp .env.example .env      # set JWT_SECRET (≥32 chars) and POSTGRES_PASSWORD
docker compose up -d --build
```

| URL | What |
|---|---|
| http://localhost:8080/cards/ | Business Card Intelligence web app |
| http://localhost:8080/api/v1/docs | OpenAPI (Swagger UI) |
| http://localhost:8080/api/v1/health | Liveness |
| http://localhost:8080/api/v1/health/ready | Readiness: database, broker, storage, OCR providers |

The port comes from `HTTP_PORT` (default 8080). Only the gateway publishes a port.

### Services

| Service | Image | Notes |
|---|---|---|
| postgres | postgres:16-alpine | volume `pgdata`, healthcheck `pg_isready` |
| redis | redis:7-alpine | broker + rate limits, AOF persistence |
| migrate | ocr-suite/api | `alembic upgrade head`, exits 0; api waits for it |
| api | ocr-suite/api | uvicorn, healthcheck `/api/v1/health` |
| worker | ocr-suite/api | Celery queue `ocr`, PaddleOCR + Tesseract baked in |
| beat | ocr-suite/api | daily retention purge |
| business-card-web | nginx static | built SPA |
| gateway | nginx:1.27-alpine | routing, security headers, upload size |

Verified on 2026-09-30 (Windows 11, Docker Desktop 29): all services up, api/worker/gateway/
web healthy, migration `0001` applied, readiness `ready` with paddleocr and tesseract available,
Playwright E2E and `tests/integration/workflows.py` passing through the gateway.

### Useful commands

```bash
docker compose ps
docker compose logs -f worker
docker compose exec postgres psql -U ocr -d ocr -c "select version_num from alembic_version"
docker compose run --rm api pytest                       # API tests inside the image
docker compose down            # keep data;   docker compose down -v  deletes volumes
```

## Overrides and profiles

| Command | Status |
|---|---|
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` — hot reload, api on 127.0.0.1:8000, db/redis exposed on localhost | configured, not tested in this round |
| `-f docker-compose.gpu.yml` — GPU worker (`worker-gpu.Dockerfile`, CUDA paddle, server det model) | configured, **not tested** |
| `-f docker-compose.prod.yml` — TLS gateway, restart always, resource limits, worker replicas | configured, **not tested** (see [production.md](production.md)) |
| `--profile minio` + `STORAGE_BACKEND=s3` | configured, not tested |
| `--profile clamav` + `MALWARE_SCANNER=clamav` | configured, not tested |
| `--profile monitoring` — Prometheus :9090 and Grafana (`GRAFANA_ADMIN_PASSWORD`) | configured, not tested |

## Resource notes

The worker peaks around 1 GB RSS with PaddleOCR on CPU (measured by the evaluation). The API
image is ~2.7 GB (paddle, opencv, tesseract, fonts, models). Paddle inference is serialised per
process; to scale, add worker replicas, not threads.

## Troubleshooting

* `migrate` exits 1 with `error parsing value for field "cors_origins"` — fixed on 2026-09-30:
  an empty `CORS_ORIGINS` is now accepted (comma-separated list; empty = same-origin only).
* Model download fails at build — the build needs internet once; afterwards the image runs offline.
