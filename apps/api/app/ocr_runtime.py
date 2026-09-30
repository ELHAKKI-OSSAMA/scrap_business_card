from __future__ import annotations

import threading

from app.config import get_settings
from ocr_core import OcrEngine, OcrProvider, OcrSettings, get_provider

_lock = threading.Lock()
_override: OcrProvider | None = None


def ocr_settings() -> OcrSettings:
    s = get_settings()
    return OcrSettings(
        provider=s.ocr_provider,
        fallback=None if s.ocr_fallback_provider == "none" else s.ocr_fallback_provider,
        device=s.ocr_device,
        paddle_det_model=s.ocr_det_model,
        use_orientation_model=s.ocr_use_orientation_model,
    )


def set_provider_override(provider: OcrProvider | None) -> None:
    """Test hook only (dependency injection of a recorded-output provider in unit tests)."""
    global _override
    _override = provider


def get_engine(provider_name: str | None = None) -> OcrEngine:
    with _lock:
        provider = _override if _override is not None else get_provider(ocr_settings(), provider_name)
    return OcrEngine(provider)
