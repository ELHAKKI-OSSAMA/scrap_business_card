"""Vercel Python function: the whole FastAPI backend behind /api/*.

Cloud-only mode: OCR and extraction by Gemma 4 on Ollama Cloud (OCR_PROVIDER=ollama), images in
S3-compatible storage (STORAGE_BACKEND=s3, e.g. Supabase Storage), data in PostgreSQL
(DATABASE_URL, e.g. Supabase pooler), jobs run inside the request (JOB_EXECUTION=sync).
See docs/deployment/vercel.md.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for rel in (
    "apps/api",
    "packages/shared-types",
    "packages/ocr-core",
    "packages/language-detection",
    "packages/document-preprocessing",
    "packages/extraction",
    "packages/validation",
):
    sys.path.insert(0, str(ROOT / rel))

# serverless defaults; explicit environment variables still win
os.environ.setdefault("OCR_PROVIDER", "ollama")
os.environ.setdefault("OCR_FALLBACK_PROVIDER", "none")
os.environ.setdefault("JOB_EXECUTION", "sync")
os.environ.setdefault("STORAGE_BACKEND", "s3")
os.environ.setdefault("LLM_PROVIDER", "none")
os.environ.setdefault("DB_SERVERLESS", "true")
os.environ.setdefault("METRICS_ENABLED", "false")

from app.main import app  # noqa: E402,F401
