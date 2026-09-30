"""Recorded-output OCR provider for API tests (TEST DOUBLE – never registered in the app).

The lines below are real PaddleOCR 3.3.3 outputs captured from synthetic samples, with boxes
scaled relative to the input image so the geometry stays consistent for any image size."""

from __future__ import annotations

from ocr_core.base import Availability, RawLine
from shared_types import ModelInfo

BUSINESS_CARD = [
    ((0.16, 0.10, 0.70, 0.18), "Pr. Youssef EL AMRANI", 0.99),
    ((0.16, 0.22, 0.40, 0.27), "Professeur", 0.99),
    ((0.16, 0.30, 0.55, 0.36), "Université Hassan II", 0.98),
    ((0.70, 0.52, 0.97, 0.60), "سلمى الإدريسي", 0.97),
    ((0.05, 0.66, 0.50, 0.71), "Mob : +212 6 97 49 89 21", 0.99),
    ((0.05, 0.73, 0.50, 0.78), "Tél : +212 5 22 34 19 60", 0.99),
    ((0.05, 0.80, 0.50, 0.85), "y.elamrani@univh2c.ma", 0.99),
    ((0.05, 0.87, 0.40, 0.92), "www.univh2c.ma", 0.99),
    ((0.62, 0.66, 0.97, 0.71), "12 Avenue Mohammed V", 0.99),
    ((0.75, 0.73, 0.97, 0.78), "10000 Rabat", 0.99),
    ((0.85, 0.80, 0.97, 0.85), "Maroc", 0.99),
]


class ReplayProvider:
    name = "replay-test-double"

    def __init__(self):
        self.script = BUSINESS_CARD
        self.calls = 0

    def availability(self) -> Availability:
        return Availability(True)

    def models(self) -> list[ModelInfo]:
        return [ModelInfo(provider=self.name, task="recognition", name="recorded-paddleocr-3.3.3-output")]

    def detect_orientation(self, rgb):
        return None

    def recognize(self, rgb, scripts):
        self.calls += 1
        h, w = rgb.shape[:2]
        out = []
        for (x0, y0, x1, y1), text, score in self.script:
            poly = [[x0 * w, y0 * h], [x1 * w, y0 * h], [x1 * w, y1 * h], [x0 * w, y1 * h]]
            out.append(RawLine(polygon=poly, text=text, score=score, det_score=0.9, model="recorded"))
        return out
