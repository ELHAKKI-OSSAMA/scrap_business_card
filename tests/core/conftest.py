from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

from shared_types import BBox, OcrLine, OcrPage, Side  # noqa: E402
from language_detection import detect_line_language, direction_for, normalize_display  # noqa: E402
from ocr_core import assign_reading_order  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def make_page(side: Side, rows: list[tuple[str, tuple[float, float, float, float]]], width: int = 1000, height: int = 600, conf: float = 0.97) -> OcrPage:
    """Build an OcrPage from (text, (x, y, w, h)) tuples, running the real language/reading-order code."""
    lines = []
    for i, (text, (x, y, w, h)) in enumerate(rows):
        g = detect_line_language(text)
        lines.append(
            OcrLine(id=f"{side.value[0]}-{i}", side=side, text=text, normalized_text=normalize_display(text), bbox=BBox(x=x, y=y, w=w, h=h), confidence=conf,
                    script=g.script, language=g.language, language_confidence=g.confidence, direction=direction_for(g.script, text), model="unit")
        )
    return OcrPage(side=side, width=width, height=height, lines=assign_reading_order(lines))


@pytest.fixture
def page_factory():
    return make_page


def paddle_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("paddleocr") is not None
