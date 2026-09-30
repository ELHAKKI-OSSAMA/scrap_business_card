from __future__ import annotations

import cv2
import numpy as np

from shared_types import QualityReport


def assess_quality(rgb: np.ndarray) -> QualityReport:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    # Normalise blur measurement to a ~1000px long side so the threshold is size independent.
    scale = 1000 / max(h, w)
    probe = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    blur = float(cv2.Laplacian(probe, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    low_res = max(h, w) < 800
    blurry = blur < 60
    dark = brightness < 70
    low_contrast = contrast < 30
    warnings: list[str] = []
    if low_res:
        warnings.append("low_resolution")
    if blurry:
        warnings.append("blurry")
    if dark:
        warnings.append("dark")
    if low_contrast:
        warnings.append("low_contrast")
    return QualityReport(
        width=w,
        height=h,
        blur_score=round(blur, 2),
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        is_low_resolution=low_res,
        is_blurry=blurry,
        is_dark=dark,
        is_low_contrast=low_contrast,
        warnings=warnings,
    )
