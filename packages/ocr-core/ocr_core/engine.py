"""Shared OCR pipeline: preprocessing -> orientation -> detection/recognition -> script &
language per line -> normalization -> reading order -> QR. Product-specific extraction runs
afterwards on the resulting ``OcrPage`` objects."""

from __future__ import annotations

import time

import numpy as np

from document_preprocessing import PreprocessOptions, preprocess, rotate_quadrant
from language_detection import detect_line_language, direction_for, has_persian_codepoints, normalize_display
from ocr_core.base import OcrProvider, RawLine, polygon_to_bbox
from ocr_core.qr import decode_qr_codes
from ocr_core.reading_order import assign_reading_order
from shared_types import BBox, ModelInfo, OcrLine, OcrPage, PreprocessingStep, Side

ALL_SCRIPTS = {"latin", "arabic"}


def scripts_for_languages(languages: list[str] | None) -> set[str]:
    """Map requested languages to recognizers. French and English share the Latin model;
    English-only requests use the English-specialised model."""
    if not languages:
        return set(ALL_SCRIPTS)
    langs = {l.lower() for l in languages}
    scripts: set[str] = set()
    if "ar" in langs:
        scripts.add("arabic")
    if "fr" in langs or ("en" in langs and len(langs - {"en"}) > 0):
        scripts.add("latin")
    elif "en" in langs:
        scripts.add("en")
    return scripts or set(ALL_SCRIPTS)


def _mean_score(lines: list[RawLine]) -> float:
    weighted = [(l.score or 0) * max(1, len(l.text)) for l in lines if l.text.strip()]
    chars = sum(max(1, len(l.text)) for l in lines if l.text.strip())
    return sum(weighted) / chars if chars else 0.0


def _to_lines(raw: list[RawLine], side: Side) -> list[OcrLine]:
    out: list[OcrLine] = []
    prefix = side.value[0]
    for i, r in enumerate(raw):
        x, y, w, h = polygon_to_bbox(r.polygon)
        guess = detect_line_language(r.text)
        alts = list(r.alternatives)
        if r.flags:
            alts.append({"flags": r.flags})
        if has_persian_codepoints(r.text):
            alts.append({"flags": ["persian_codepoints_normalized"]})
        out.append(
            OcrLine(
                id=f"{prefix}-{i}",
                side=side,
                text=r.text,
                normalized_text=normalize_display(r.text),
                bbox=BBox(x=x, y=y, w=w, h=h),
                polygon=[[round(a, 1), round(b, 1)] for a, b in r.polygon],
                confidence=round(r.score, 4) if r.score is not None else None,
                detection_confidence=round(r.det_score, 4) if r.det_score is not None else None,
                script=guess.script,
                language=guess.language,
                language_confidence=guess.confidence,
                direction=direction_for(guess.script, r.text),
                model=r.model,
                alternatives=alts,
            )
        )
    return out


class OcrEngine:
    def __init__(self, provider: OcrProvider, preprocess_options: PreprocessOptions | None = None):
        self.provider = provider
        self.preprocess_options = preprocess_options or PreprocessOptions()

    def process_page(self, rgb: np.ndarray, side: Side, *, languages: list[str] | None = None, exif_transposed: bool = False) -> tuple[OcrPage, np.ndarray]:
        """Returns the OCR page and the processed image the coordinates refer to."""
        t0 = time.perf_counter()
        scripts = scripts_for_languages(languages)
        pre = preprocess(rgb, self.preprocess_options, exif_transposed=exif_transposed)
        img = pre.rgb
        steps = list(pre.steps)
        models: list[ModelInfo] = []

        rotation = 0
        orient = self.provider.detect_orientation(img)
        if orient is not None:
            deg, conf = orient
            if deg and conf >= 0.8:
                img = rotate_quadrant(img, deg)
                rotation = deg
            steps.append(PreprocessingStep(name="rotation_correction", applied=bool(rotation), details={"method": "model", "degrees_cw": deg, "confidence": round(conf, 3)}))
        raw = self.provider.recognize(img, scripts)

        if orient is None:
            # heuristic fallback: mostly-vertical boxes suggest a 90° rotation; try both and keep the better
            vertical = sum(1 for r in raw if (lambda b: b[3] > 1.5 * b[2])(polygon_to_bbox(r.polygon)))
            if raw and vertical / len(raw) > 0.6:
                best = (_mean_score(raw), 0, img, raw)
                for deg in (90, 270):
                    cand_img = rotate_quadrant(img, deg)
                    cand = self.provider.recognize(cand_img, scripts)
                    score = _mean_score(cand)
                    if score > best[0] + 0.05:
                        best = (score, deg, cand_img, cand)
                _, rotation, img, raw = best
            steps.append(PreprocessingStep(name="rotation_correction", applied=bool(rotation), details={"method": "box_aspect_heuristic", "degrees_cw": rotation}))

        lines = assign_reading_order(_to_lines(raw, side))
        qr_codes = decode_qr_codes(img, side)
        models.extend(self.provider.models())
        models.append(ModelInfo(provider="opencv", task="qr", name="cv2.QRCodeDetector", version=_cv_version()))
        page = OcrPage(
            side=side,
            width=int(img.shape[1]),
            height=int(img.shape[0]),
            lines=lines,
            qr_codes=qr_codes,
            quality=pre.quality,
            preprocessing=steps,
            models=models,
            processing_ms=int((time.perf_counter() - t0) * 1000),
            rotation_applied=rotation,
        )
        return page, img


def _cv_version() -> str:
    import cv2

    return cv2.__version__
