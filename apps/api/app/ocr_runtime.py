from __future__ import annotations

import threading

from app.config import get_settings
from ocr_core import OcrProvider

_lock = threading.Lock()
_override: OcrProvider | None = None
_vision_client = None


def ocr_settings():
    from ocr_core import OcrSettings

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


def vision_client():
    """One Ollama client per process so the API-key rotation index survives between jobs."""
    global _vision_client
    with _lock:
        if _vision_client is None:
            from extraction import OllamaVisionClient

            s = get_settings()
            _vision_client = OllamaVisionClient(model=s.ollama_model, api_keys=s.ollama_key_list, base_url=s.ollama_base_url, timeout=s.llm_timeout_s)
        return _vision_client


def cloud_mode() -> bool:
    return _override is None and get_settings().ocr_provider == "ollama"


def get_engine(provider_name: str | None = None):
    if cloud_mode():
        from extraction import OllamaCloudEngine

        return OllamaCloudEngine(vision_client())  # one per job: it carries the parsed fields
    from ocr_core import OcrEngine, get_provider

    with _lock:
        provider = _override if _override is not None else get_provider(ocr_settings(), provider_name)
    return OcrEngine(provider)


def provider_status() -> list[dict]:
    if cloud_mode():
        s = get_settings()
        ok = bool(s.ollama_key_list) or not s.ollama_base_url.startswith("https://ollama.com")
        return [{"provider": "ollama", "available": ok, "reason": None if ok else "OLLAMA_KEYS not set", "external": True, "model": s.ollama_model}]
    from ocr_core import provider_status as status

    return status(ocr_settings())
