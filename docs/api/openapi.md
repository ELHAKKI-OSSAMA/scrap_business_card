# API

* Machine-readable spec: [`openapi.json`](openapi.json) (exported from the running stack on
  2026-09-30; OpenAPI 3.1, "Multilingual OCR Suite API" 0.1.0, 33 paths).
* Interactive docs on a running stack: `/api/v1/docs` (Swagger UI) and `/api/v1/redoc`.
* Base path: `/api/v1`. JSON everywhere except uploads (multipart) and exports.

## Authentication

```http
POST /api/v1/auth/register   {"email","password"(≥10),"display_name"?,"locale":"en|fr|ar"}  → 201 tokens
POST /api/v1/auth/login      {"email","password"}                                             → tokens
POST /api/v1/auth/refresh    {"refresh_token"}   → new pair (old one revoked; reuse revokes family)
POST /api/v1/auth/logout     {"refresh_token"}   → 204
```

Send `Authorization: Bearer <access_token>` (15 min lifetime).

## Products

All document routes live under `/business-cards`.

| Method | Path | Notes |
|---|---|---|
| POST | `/business-cards` | `{"title"?, "client_ref"?}` — `client_ref` makes creation idempotent |
| GET | `/business-cards` | `q` (accent/case/Arabic-diacritic-insensitive), `status`, `review_status`, `language`, paging |
| GET | `/business-cards/{id}` | document, images, latest job, `data` (current fields), `machine_data`, `ocr` (pages → lines, regions) |
| POST | `/business-cards/{id}/images?side=front\|back` | multipart `file`; same bytes again = no-op |
| POST | `/business-cards/{id}/process` | 202 `{"job_id"}`; unchanged input returns the existing job |
| GET | `/jobs/{job_id}` | `queued \| running \| completed \| failed`, `error_code` |
| PATCH | `/business-cards/{id}/fields` | `{"changes":[{"path","op":"set\|append\|remove\|verify","value"}],"expected_version"?}` — 409 on version conflict, 422 on invalid values (e.g. malformed email) |
| POST | `/business-cards/{id}/review` | set document review status |
| GET | `/business-cards/{id}/history` | correction history |
| GET | `/business-cards/{id}/export?format=` | `json`, `csv`, `vcf` |
| GET | `/business-cards/export?format=&q=` | bulk export |
| DELETE | `/business-cards/{id}` | soft delete, purged after retention |
| GET | `/business-cards/{id}/duplicates` | suggestions only |
| POST | `/business-cards/{id}/merge` | explicit merge, recorded in history |

System: `GET /health`, `GET /health/ready`, `GET /models` (installed models, verified
capabilities, handwriting status), `POST /translate` (optional, disabled unless configured).

## Errors

```json
{"error": {"code": "not_found", "message": "…", "details": {}, "request_id": "…"}}
```

Documents in another workspace return `404`, not `403`.

## Field values

Every extracted field is a `FieldValue`:

```json
{"value": "Rabat", "original_value": "RABAT", "normalized_value": "rabat",
 "confidence": 0.586, "source_region_ids": ["…"], "extraction_method": "rule",
 "review_status": "needs_review"}
```

`confidence` is `null` when there is no evidence. Phones add `e164` and `type`.

## Example (curl)

```bash
API=http://localhost:8080/api/v1
TOKEN=$(curl -s $API/auth/login -H 'content-type: application/json' \
  -d '{"email":"you@example.com","password":"…"}' | jq -r .access_token)
ID=$(curl -s $API/business-cards -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{}' | jq -r .id)
curl -s "$API/business-cards/$ID/images?side=front" -H "authorization: Bearer $TOKEN" -F file=@card.jpg >/dev/null
JOB=$(curl -s -X POST $API/business-cards/$ID/process -H "authorization: Bearer $TOKEN" | jq -r .job_id)
curl -s $API/jobs/$JOB -H "authorization: Bearer $TOKEN"            # poll until completed
curl -s "$API/business-cards/$ID/export?format=vcf" -H "authorization: Bearer $TOKEN"
```

A complete scripted example is `tests/integration/workflows.py`.
