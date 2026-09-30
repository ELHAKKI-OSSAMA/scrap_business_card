"""Field confidence.

Definition (documented in docs/models/evaluation.md):

    field_confidence = ocr_confidence × method_reliability × validation_factor

* ``ocr_confidence``: character-weighted mean recognizer score of the evidence lines
  (PaddleOCR CTC score / Tesseract word conf ÷ 100). Not calibrated.
* ``method_reliability``: fixed prior per extraction method (below). These are engineering
  priors, **not** measured accuracies; they only rank fields for review.
* ``validation_factor``: 1.0 when a deterministic validator accepted the value (valid e-mail,
  valid phone number), 0.6 when validation failed, 0.85 when no validator applies.

The value is ``None`` when there is no OCR evidence (e.g. manual entry).
"""

from __future__ import annotations

from shared_types import OcrLine

METHOD_RELIABILITY = {
    "ocr": 1.0,
    "rule": 0.95,
    "qr": 0.95,
    "layout": 0.7,
    "ner": 0.75,
    "llm": 0.7,
    "manual": 1.0,
}


def combine_confidence(lines: list[OcrLine]) -> float | None:
    scored = [(l.confidence, max(1, len(l.text))) for l in lines if l.confidence is not None]
    if not scored:
        return None
    total = sum(w for _, w in scored)
    return sum(c * w for c, w in scored) / total


def field_confidence(lines: list[OcrLine], method: str, validated: bool | None = None) -> float | None:
    base = combine_confidence(lines)
    if base is None:
        return None
    factor = 0.85 if validated is None else (1.0 if validated else 0.6)
    return round(max(0.0, min(1.0, base * METHOD_RELIABILITY.get(method, 0.7) * factor)), 3)
