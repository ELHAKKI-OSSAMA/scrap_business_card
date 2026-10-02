"""OCR core. Submodules are loaded on first use so that importing ``ocr_core`` (e.g. for
``OcrUnavailableError`` or the Ollama cloud engine) never pulls OpenCV / Paddle / Tesseract."""

from ocr_core.base import Availability, OcrProvider, OcrUnavailableError, RawLine, polygon_to_bbox

_LAZY = {
    "OcrEngine": "ocr_core.engine",
    "scripts_for_languages": "ocr_core.engine",
    "classify_qr": "ocr_core.qr",
    "decode_qr_codes": "ocr_core.qr",
    "is_safe_url": "ocr_core.qr",
    "assign_reading_order": "ocr_core.reading_order",
    "OcrSettings": "ocr_core.registry",
    "get_provider": "ocr_core.registry",
    "provider_status": "ocr_core.registry",
    "choose_hypothesis": "ocr_core.selection",
}


def __getattr__(name: str):
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'ocr_core' has no attribute {name!r}")


__all__ = ["Availability", "OcrProvider", "OcrUnavailableError", "RawLine", "polygon_to_bbox", *_LAZY]
