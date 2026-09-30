# syntax=docker/dockerfile:1.7
# Optional GPU worker. Requires an NVIDIA GPU, a recent driver and the NVIDIA Container Toolkit.
# paddlepaddle-gpu wheels are published on Paddle's own index per CUDA version.
FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PADDLE_PDX_CACHE_HOME=/opt/models \
    DISABLE_MODEL_SOURCE_CHECK=True \
    UV_PYTHON_INSTALL_DIR=/opt/python

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates tesseract-ocr tesseract-ocr-ara tesseract-ocr-fra tesseract-ocr-eng \
        libgl1 libglib2.0-0 libgomp1 fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
RUN uv venv --python 3.12 /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" VIRTUAL_ENV=/opt/venv

WORKDIR /srv
ARG PADDLE_GPU_INDEX=https://www.paddlepaddle.org.cn/packages/stable/cu126/
RUN uv pip install "paddlepaddle-gpu==3.2.2" -i "${PADDLE_GPU_INDEX}" --index-strategy unsafe-best-match
COPY packages packages
RUN uv pip install "./packages[tesseract,synthetic]" "paddleocr==3.3.3"
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/app apps/api/app
COPY apps/api/alembic apps/api/alembic
COPY apps/api/alembic.ini apps/api/alembic.ini
RUN uv pip install ./apps/api
COPY infrastructure/scripts/download_models.py /tmp/download_models.py
RUN mkdir -p /opt/models && python /tmp/download_models.py > /opt/models/installed.json

RUN useradd --create-home --uid 10001 app && mkdir -p /data/storage && chown -R app:app /data /opt/models
USER app
WORKDIR /srv/apps/api
ENV OCR_DEVICE=gpu:0
CMD ["celery", "-A", "app.worker", "worker", "-Q", "ocr", "--concurrency", "1", "--loglevel", "INFO"]
