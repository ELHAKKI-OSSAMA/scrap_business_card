# syntax=docker/dockerfile:1.7
# API + Celery worker image (CPU). One image, two commands.
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PADDLE_PDX_CACHE_HOME=/opt/models \
    DISABLE_MODEL_SOURCE_CHECK=True

# tesseract (+ Arabic/French/English traineddata) for the fallback/baseline provider,
# libgl/glib for opencv, libgomp for paddle, fonts-noto for synthetic sample rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-ara tesseract-ocr-fra tesseract-ocr-eng \
        libgl1 libglib2.0-0 libgomp1 curl fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY packages/pyproject.toml packages/pyproject.toml
COPY packages/shared-types/shared_types packages/shared-types/shared_types
COPY packages/ocr-core/ocr_core packages/ocr-core/ocr_core
COPY packages/language-detection/language_detection packages/language-detection/language_detection
COPY packages/document-preprocessing/document_preprocessing packages/document-preprocessing/document_preprocessing
COPY packages/extraction/extraction packages/extraction/extraction
COPY packages/validation/validation packages/validation/validation
RUN pip install "./packages[paddle,tesseract,synthetic]"

COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/app apps/api/app
RUN pip install ./apps/api

# bake OCR weights into the image (offline, reproducible start-up)
COPY infrastructure/scripts/download_models.py /tmp/download_models.py
RUN mkdir -p /opt/models && python /tmp/download_models.py > /opt/models/installed.json && rm /tmp/download_models.py

COPY apps/api/alembic apps/api/alembic
COPY apps/api/alembic.ini apps/api/alembic.ini
COPY apps/api/tests apps/api/tests
COPY tests/core tests/core
COPY ml ml
COPY pytest.ini pytest.ini

RUN useradd --create-home --uid 10001 app && mkdir -p /data/storage && chown -R app:app /data /opt/models
USER app
WORKDIR /srv/apps/api
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 CMD curl -fsS http://localhost:8000/api/v1/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
