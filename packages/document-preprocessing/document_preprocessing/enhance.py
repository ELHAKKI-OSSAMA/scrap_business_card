from __future__ import annotations

import cv2
import numpy as np

from shared_types import PreprocessingStep, QualityReport


def enhance(rgb: np.ndarray, quality: QualityReport) -> tuple[np.ndarray, list[PreprocessingStep]]:
    """Quality-driven enhancement. Each step only runs when the quality report asks for it,
    because over-processing clean scans measurably hurts recognition."""
    steps: list[PreprocessingStep] = []
    out = rgb

    if quality.is_low_resolution:
        factor = min(2.5, 1200 / max(out.shape[:2]))
        if factor > 1.05:
            out = cv2.resize(out, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)
            steps.append(PreprocessingStep(name="upscale", applied=True, details={"factor": round(factor, 2)}))
    if not any(s.name == "upscale" for s in steps):
        steps.append(PreprocessingStep(name="upscale", applied=False))

    noisy = quality.contrast > 0 and quality.blur_score > 1500  # very high Laplacian variance = speckle noise
    if noisy or quality.is_dark:
        out = cv2.fastNlMeansDenoisingColored(out, None, 5, 5, 7, 21)
        steps.append(PreprocessingStep(name="denoise", applied=True, details={"method": "fastNlMeans", "h": 5}))
    else:
        steps.append(PreprocessingStep(name="denoise", applied=False))

    if quality.is_low_contrast or quality.is_dark or quality.brightness > 235:
        lab = cv2.cvtColor(out, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
        out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)
        steps.append(PreprocessingStep(name="contrast_illumination", applied=True, details={"method": "CLAHE", "clip": 2.0}))
    else:
        steps.append(PreprocessingStep(name="contrast_illumination", applied=False))
    return np.ascontiguousarray(out), steps
