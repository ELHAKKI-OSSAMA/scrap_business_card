"""Low-level visual region detector used by the business-card layout heuristics (logo candidates).

These return *candidates* with a heuristic score; they are not trained detectors."""

from __future__ import annotations

import cv2
import numpy as np

from shared_types import BBox


def detect_color_patches(rgb: np.ndarray, *, min_area_ratio: float = 0.004, max_area_ratio: float = 0.12) -> list[tuple[BBox, float]]:
    """Compact, strongly coloured rectangles – typical of logos."""
    h, w = rgb.shape[:2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    mask = ((sat > 70) & (hsv[:, :, 2] > 40)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out: list[tuple[BBox, float]] = []
    total = h * w
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if not (min_area_ratio * total <= area <= max_area_ratio * total):
            continue
        fill = cv2.contourArea(c) / max(area, 1)
        aspect = bw / max(bh, 1)
        if fill < 0.55 or not (0.4 <= aspect <= 2.5):
            continue
        score = round(float(min(1.0, 0.4 + 0.6 * fill) * (1.0 if 0.6 <= aspect <= 1.6 else 0.8)), 3)
        out.append((BBox(x=x, y=y, w=bw, h=bh), score))
    return out
