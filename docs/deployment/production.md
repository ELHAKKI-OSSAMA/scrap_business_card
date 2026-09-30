# Production deployment

> The production override exists but **has not been deployed or tested**. Treat this page as a
> checklist, and validate each step in a staging environment first.

## Command

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The override:

* switches the gateway to `infrastructure/nginx/gateway.tls.conf` (ports 80/443, HSTS, HTTP→HTTPS,
  ACME webroot `certbot-www`), mounting certificates from `TLS_CERT_DIR` (default `./certs`,
  expects `fullchain.pem` and `privkey.pem`);
* sets `ENVIRONMENT=production` and `ALLOW_REGISTRATION=false` by default;
* adds `restart: always` and CPU/memory limits (api 2 CPU/2 GB, worker 4 CPU/4 GB);
* runs `WORKER_REPLICAS` workers (default 2).

## Required decisions / inputs (owner)

These need the project owner and cannot be defaulted:

1. **Domain and TLS certificates** (Let's Encrypt or organisational CA).
2. **Production secrets**: `JWT_SECRET`, `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`, S3 keys
   if used — from a secret manager, never committed.
3. **Hosting** (VM size: plan ≥ 4 vCPU / 8 GB for api + 2 CPU workers; a GPU host if using the
   GPU override, which is untested).
4. **Retention periods and a privacy notice** ([../security/privacy.md](../security/privacy.md)).
5. Whether to enable the optional **LLM** or **translation** providers (paid/external services,
   data leaves the host).

## Checklist

- [ ] `.env` from a secret manager; `ENVIRONMENT=production`; `CORS_ORIGINS` only if the web apps
      are served from a different origin.
- [ ] Certificates present; `https://<domain>/api/v1/health/ready` returns `ready`.
- [ ] `STORAGE_BACKEND=s3` with a private, encrypted bucket, or a backed-up `storage` volume.
- [ ] Nightly encrypted Postgres backups (`pg_dump`) and a tested restore.
- [ ] `--profile monitoring` or an external Prometheus scraping `api:8000/api/v1/metrics` and the
      worker; alerts on job failure rate and queue depth.
- [ ] Gateway access-log format without query strings (search terms may contain names).
- [ ] `--profile clamav` if uploads come from untrusted users.
- [ ] Run `tests/integration/workflows.py --base https://<domain>/api/v1` against staging.
- [ ] Mobile release build pointed at the HTTPS URL (`--dart-define=API_BASE=https://<domain>/api/v1`).

## Upgrades

Build new images with a new `IMAGE_TAG`; `migrate` runs `alembic upgrade head` before the api
starts. Re-run the evaluation when changing OCR models.
