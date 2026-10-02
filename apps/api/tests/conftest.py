from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="ocr-suite-test-"))
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", f"sqlite:///{(_TMP / 'test.db').as_posix()}"),
        "JOB_EXECUTION": "sync",
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_PATH": str(_TMP / "storage"),
        "REDIS_URL": "",
        "JWT_SECRET": "test-secret-test-secret-test-secret-1234",
        "RATE_LIMIT_AUTH_PER_MINUTE": "1000",
        "RATE_LIMIT_UPLOAD_PER_MINUTE": "1000",
        "OCR_USE_ORIENTATION_MODEL": "false",
        "DISABLE_MODEL_SOURCE_CHECK": "True",
        # never call an external LLM from tests, whatever the developer's .env says
        "LLM_PROVIDER": "none",
        "OLLAMA_KEYS": "",
    }
)

ROOT = Path(__file__).resolve().parents[3]
SYNTH = ROOT / "ml" / "datasets" / "synthetic" / "out"
sys.path.insert(0, str(Path(__file__).parent))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    cfg = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")  # the migration itself is under test
    yield


@pytest.fixture(scope="session")
def app():
    from app.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    from app.ratelimit import reset_rate_limits

    reset_rate_limits()
    with TestClient(app) as c:
        yield c


_counter = {"n": 0}


def _register(client, name: str) -> dict:
    _counter["n"] += 1
    email = f"{name}{_counter['n']}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "correct horse battery", "display_name": name})
    assert r.status_code == 201, r.text
    tok = r.json()
    return {"email": email, "headers": {"Authorization": f"Bearer {tok['access_token']}"}, "refresh": tok["refresh_token"]}


@pytest.fixture()
def alice(client):
    return _register(client, "alice")


@pytest.fixture()
def bob(client):
    return _register(client, "bob")


def png_bytes(w: int = 400, h: int = 250, color=(240, 240, 240)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def replay_provider():
    """Test double: returns recorded OCR lines (captured from PaddleOCR on the synthetic card
    bc-ar_fr-000). Used only to test API/DB logic quickly; real-model tests are marked `ocr`."""
    from app.ocr_runtime import set_provider_override
    from replay import ReplayProvider

    prov = ReplayProvider()
    set_provider_override(prov)
    yield prov
    set_provider_override(None)
