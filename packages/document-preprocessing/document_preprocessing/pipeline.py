from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from document_preprocessing.enhance import enhance
from document_preprocessing.geometry import detect_document_quad, estimate_skew_angle, four_point_transform, rotate_bound
from document_preprocessing.quality import assess_quality
from shared_types import PreprocessingStep, QualityReport


@dataclass
class PreprocessOptions:
    perspective: bool = True
    deskew: bool = True
    enhance: bool = True
    min_skew_deg: float = 0.7


@dataclass
class PreprocessResult:
    rgb: np.ndarray
    quality: QualityReport
    steps: list[PreprocessingStep] = field(default_factory=list)


def preprocess(rgb: np.ndarray, options: PreprocessOptions | None = None, *, exif_transposed: bool = False) -> PreprocessResult:
    """Steps 3-9 of the pipeline (EXIF was applied during validation)."""
    opts = options or PreprocessOptions()
    steps = [PreprocessingStep(name="exif_orientation", applied=exif_transposed)]
    quality = assess_quality(rgb)
    steps.append(PreprocessingStep(name="quality_assessment", applied=True, details={"warnings": quality.warnings}))

    out = rgb
    if opts.perspective:
        quad = detect_document_quad(out)
        if quad is not None:
            out = four_point_transform(out, quad)
            steps.append(PreprocessingStep(name="perspective_correction", applied=True, details={"quad": quad.round(1).tolist()}))
        else:
            steps.append(PreprocessingStep(name="perspective_correction", applied=False, details={"reason": "no_boundary_found"}))

    if opts.deskew:
        angle = estimate_skew_angle(out)
        if abs(angle) >= opts.min_skew_deg:
            out = rotate_bound(out, angle)
            steps.append(PreprocessingStep(name="deskew", applied=True, details={"angle_deg": round(angle, 2)}))
        else:
            steps.append(PreprocessingStep(name="deskew", applied=False, details={"angle_deg": round(angle, 2)}))

    if opts.enhance:
        out, enh_steps = enhance(out, quality)
        steps.extend(enh_steps)
    return PreprocessResult(rgb=out, quality=quality, steps=steps)
