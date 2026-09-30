from __future__ import annotations

import sys

import numpy as np

from conftest import ROOT

sys.path.insert(0, str(ROOT / "ml" / "datasets" / "synthetic"))


def render_line(text: str, size: int = 40) -> np.ndarray:
    from generate import Canvas

    c = Canvas(1000, 110, bg=(255, 255, 255))
    if any("؀" <= ch <= "ۿ" for ch in text):
        c.text(980, 30, text, size, align="right")
    else:
        c.text(20, 30, text, size)
    return np.asarray(c.img)
