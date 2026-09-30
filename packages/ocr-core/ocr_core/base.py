from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import numpy as np

from shared_types import ModelInfo


class OcrUnavailableError(RuntimeError):
    """Raised when a requested OCR provider or model is not installed. Never swallowed into
    a fake result – the job fails with ``ocr_engine_unavailable``."""

    code = "ocr_engine_unavailable"


@dataclass
class RawLine:
    polygon: list[list[float]]  # 4 points, image coordinates of the processed image
    text: str
    score: float | None
    det_score: float | None = None
    model: str | None = None
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


@dataclass
class Availability:
    available: bool
    reason: str | None = None


@runtime_checkable
class OcrProvider(Protocol):
    name: str

    def availability(self) -> Availability: ...

    def models(self) -> list[ModelInfo]: ...

    def recognize(self, rgb: np.ndarray, scripts: set[str]) -> list[RawLine]:
        """Detect and recognize text lines. ``scripts`` ⊆ {"latin", "arabic", "en"}."""
        ...

    def detect_orientation(self, rgb: np.ndarray) -> tuple[int, float] | None:
        """Return (clockwise degrees to rotate, confidence) or None if unsupported."""
        ...


def polygon_to_bbox(poly: list[list[float]] | np.ndarray) -> tuple[float, float, float, float]:
    arr = np.asarray(poly, dtype=float).reshape(-1, 2)
    x0, y0 = arr.min(axis=0)
    x1, y1 = arr.max(axis=0)
    return float(x0), float(y0), float(x1 - x0), float(y1 - y0)
