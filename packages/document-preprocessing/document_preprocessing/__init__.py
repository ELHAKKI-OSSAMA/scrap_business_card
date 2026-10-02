"""Upload validation (Pillow + NumPy only) is imported eagerly; everything that needs OpenCV is
loaded on first use, so the lightweight cloud deployment (OCR_PROVIDER=ollama, e.g. on Vercel)
never imports cv2."""

from document_preprocessing.validation import (
    ALLOWED_MIME_TYPES,
    ImageValidationError,
    ValidatedImage,
    sniff_mime,
    validate_image_bytes,
)

_LAZY = {
    "assess_quality": "document_preprocessing.quality",
    "detect_document_quad": "document_preprocessing.geometry",
    "estimate_skew_angle": "document_preprocessing.geometry",
    "four_point_transform": "document_preprocessing.geometry",
    "rotate_bound": "document_preprocessing.geometry",
    "rotate_quadrant": "document_preprocessing.geometry",
    "enhance": "document_preprocessing.enhance",
    "PreprocessOptions": "document_preprocessing.pipeline",
    "PreprocessResult": "document_preprocessing.pipeline",
    "preprocess": "document_preprocessing.pipeline",
    "detect_color_patches": "document_preprocessing.regions",
}


def __getattr__(name: str):
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'document_preprocessing' has no attribute {name!r}")


__all__ = ["ALLOWED_MIME_TYPES", "ImageValidationError", "ValidatedImage", "sniff_mime", "validate_image_bytes", *_LAZY]
