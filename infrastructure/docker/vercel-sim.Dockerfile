# Local stand-in for the Vercel Python function: same requirements.txt, same api/index.py entry,
# nothing else installed (no Paddle, no OpenCV, no Tesseract, no Celery). Used to verify the
# cloud-only deployment before pushing it to Vercel.
FROM python:3.12-slim
WORKDIR /var/task
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && cd /usr/local/lib/python3.12/site-packages && du -smc $(ls | grep -vE "^(pip|setuptools|wheel)") | tail -1 | cut -f1 > /bundle-deps-mb.txt && cd /var/task
# not part of the Vercel bundle: alembic (migrations run from a dev machine / CI) and uvicorn (Vercel has its own server)
RUN pip install --no-cache-dir alembic==1.20.0 uvicorn==0.54.0
COPY api api
COPY apps/api/app apps/api/app
COPY apps/api/alembic apps/api/alembic
COPY apps/api/alembic.ini apps/api/alembic.ini
COPY packages/shared-types/shared_types packages/shared-types/shared_types
COPY packages/ocr-core/ocr_core packages/ocr-core/ocr_core
COPY packages/language-detection/language_detection packages/language-detection/language_detection
COPY packages/document-preprocessing/document_preprocessing packages/document-preprocessing/document_preprocessing
COPY packages/extraction/extraction packages/extraction/extraction
COPY packages/validation/validation packages/validation/validation
ENV PYTHONPATH=/var/task/apps/api:/var/task/packages/shared-types:/var/task/packages/ocr-core:/var/task/packages/language-detection:/var/task/packages/document-preprocessing:/var/task/packages/extraction:/var/task/packages/validation
EXPOSE 3000
CMD ["python", "-m", "uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "3000"]
