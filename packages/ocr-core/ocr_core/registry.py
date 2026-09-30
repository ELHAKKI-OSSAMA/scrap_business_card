from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from ocr_core.base import OcrProvider, OcrUnavailableError
from ocr_core.paddle_provider import PaddleProvider
from ocr_core.tesseract_provider import TesseractProvider

log = logging.getLogger(__name__)


@dataclass
class OcrSettings:
    provider: str = "paddleocr"  # paddleocr | tesseract
    fallback: str | None = "tesseract"  # used only if the primary is *unavailable*, and recorded
    device: str = "cpu"  # cpu | gpu:0
    paddle_det_model: str = "PP-OCRv5_mobile_det"
    use_orientation_model: bool = True


_lock = threading.Lock()
_cache: dict[tuple, OcrProvider] = {}


def build_provider(name: str, settings: OcrSettings) -> OcrProvider:
    if name == "paddleocr":
        return PaddleProvider(det_model=settings.paddle_det_model, device=settings.device, use_orientation=settings.use_orientation_model)
    if name == "tesseract":
        return TesseractProvider()
    raise OcrUnavailableError(f"unknown OCR provider '{name}'")


def get_provider(settings: OcrSettings, name: str | None = None) -> OcrProvider:
    """Return the requested provider; fall back only to a *verified available* alternative."""
    wanted = name or settings.provider
    key = (wanted, settings.device, settings.paddle_det_model, settings.use_orientation_model)
    with _lock:
        if key in _cache:
            return _cache[key]
        provider = build_provider(wanted, settings)
        av = provider.availability()
        if not av.available:
            if name is None and settings.fallback and settings.fallback != wanted:
                alt = build_provider(settings.fallback, settings)
                alt_av = alt.availability()
                if alt_av.available:
                    log.warning("OCR provider %s unavailable (%s); using fallback %s", wanted, av.reason, settings.fallback)
                    _cache[key] = alt
                    return alt
                raise OcrUnavailableError(f"{wanted}: {av.reason}; fallback {settings.fallback}: {alt_av.reason}")
            raise OcrUnavailableError(f"{wanted}: {av.reason}")
        _cache[key] = provider
        return provider


def provider_status(settings: OcrSettings) -> list[dict]:
    out = []
    for name in ("paddleocr", "tesseract"):
        p = build_provider(name, settings)
        av = p.availability()
        out.append(
            {
                "provider": name,
                "available": av.available,
                "reason": av.reason,
                "is_default": name == settings.provider,
                "models": [m.model_dump() for m in p.models()] if av.available else [],
            }
        )
    out.append(
        {
            "provider": "handwriting",
            "available": False,
            "reason": "No verified handwriting recognizer (Arabic or Latin) is installed. Handwritten text is read "
            "best-effort by the printed-text models and flagged as unverified.",
            "is_default": False,
            "models": [],
        }
    )
    return out
