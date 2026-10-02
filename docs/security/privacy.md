# Security and privacy

Business cards contain personal data (names, addresses, phone numbers, e-mails,
private messages). The system is designed to process them locally, keep them private, and
leave every consequential decision to a person.

## Data flow and external calls

* OCR, extraction and validation run inside the stack; **no external API is called by default**.
* Optional, off by default, and only to endpoints the operator configures:
  LLM enrichment (`LLM_PROVIDER`), translation (`TRANSLATION_PROVIDER`), S3 storage.
* `OCR_PROVIDER=ollama` (cloud-only mode, the Vercel deployment) sends **every card image** to
  Ollama Cloud, which reads it and proposes the fields; nothing is processed locally.
* `LLM_PROVIDER=ollama_vision` (Gemma 4 via `OLLAMA_BASE_URL`, Ollama Cloud by default) sends the
  **card image and its OCR text** to that service for every processed card. Use it only with the
  operator's/client's consent. Its answers are accepted only when grounded in the OCR text, and are
  always marked `needs_review`. Keys live in `.env` (`OLLAMA_KEYS`), never in the code; the worker
  is the only container with outbound internet (`egress` network).
* QR codes are decoded and their URLs checked (`is_safe_url`), but **never opened or fetched**.
* Model weights are baked into the image at build time; nothing is downloaded at runtime.

## Access control

* Passwords: Argon2id. Access tokens: JWT, 15 min. Refresh tokens: 14 days, rotated on every
  use, with reuse detection that revokes the whole token family.
* Every document belongs to a workspace; other workspaces get **404** (no existence leak). Tested
  in the API suite and in both E2E tests (isolation step).
* Rate limits on auth (10/min) and uploads (60/min).
* Production override sets `ALLOW_REGISTRATION=false` by default.
* Mobile: refresh token in `flutter_secure_storage` (Keystore/Keychain); drafts and images in
  app-private storage.

## Uploads

Type detected from bytes (JPEG/PNG/WebP/TIFF only), size limit (`MAX_UPLOAD_MB`, default 15),
pixel limit against decompression bombs, EXIF metadata (including GPS) stripped from the processed
copy. Optional ClamAV scanning (`--profile clamav`, `MALWARE_SCANNER=clamav`) — **not tested**.

## Integrity of results

* Raw OCR output and machine extraction are immutable; corrections are stored separately with a
  full history (`review_events`: who, when, old → new).
* No automatic merging of duplicate cards (suggestions only), no automatic translation, no
  automatic import of QR-code data.
* Exports: CSV cells starting with `= + - @` are prefixed with `'` (formula injection); UTF-8 BOM
  for Excel.
* Optional LLM output must be grounded in OCR text; document lines resembling instructions
  (prompt injection) are rejected.

## Logging and monitoring

* Application logs are structured JSON with ids, codes and durations — no request bodies, OCR
  text, images or tokens. Verified on 2026-09-30: after the workflow run, the api/worker/gateway
  logs contained none of the extracted names or emails, nor the registered account emails.
* **Known limitation**: the nginx access log records full request URLs, including search query
  strings (`GET /api/v1/business-cards?q=…`). A search term may therefore contain personal data.
  Mitigate in production by using a log format without `$args` or by restricting access to
  gateway logs.
* `/metrics` is not exposed through the gateway (404); Prometheus scrapes it on the internal network.
* Audit events record logins, exports, deletions, merges.

## Retention and deletion

* Deleting a document is a soft delete; the daily `beat` job purges it and its stored images after
  `DELETED_RETENTION_DAYS` (default 30).
* `DOCUMENT_RETENTION_DAYS` (default 0 = disabled) purges all documents older than N days.
* Deleting a mobile draft removes its private image copies.

## Transport and headers

The gateway sends CSP (`default-src 'self'`), `X-Frame-Options: DENY`, `nosniff`,
`Referrer-Policy: no-referrer`, and a Permissions-Policy. The TLS configuration
(`gateway.tls.conf`, prod override) adds HSTS — **the TLS override has not been tested**.
Debug Android builds allow cleartext HTTP to reach a local gateway; release builds do not.

## Secrets

No credentials are committed. `.env` (git-ignored) holds `JWT_SECRET`, `POSTGRES_PASSWORD` and
optional keys; Compose refuses to start without the required ones. `.env.example` contains
placeholders only. The dev demo account is in `infrastructure/scripts/dev-seed.env` for local
development only.

## Operator checklist before real data

1. Strong unique secrets; TLS enabled; registration closed or invite-only.
2. Decide the retention periods and document them to users.
3. Restrict or reformat gateway access logs (see above).
4. Enable ClamAV if files come from untrusted users, and test it.
5. Back up the Postgres and storage volumes, encrypted.
6. Consent / legal basis for processing third parties' personal data (the people on business
   cards) — a legal decision for the operator.
