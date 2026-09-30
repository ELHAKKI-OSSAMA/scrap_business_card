"""PaddleOCR 3.x adapter.

Model names are explicit (not ``lang=``) so the recognizer actually used is recorded:

* detection:   PP-OCRv5_mobile_det (default) or PP-OCRv5_server_det
* latin:       latin_PP-OCRv5_mobile_rec  (French, English and other Latin-script languages)
* en:          en_PP-OCRv5_mobile_rec     (optional English-specialised model)
* arabic:      arabic_PP-OCRv5_mobile_rec (Arabic script; printed text)
* orientation: PP-LCNet_x1_0_doc_ori      (0/90/180/270)
"""

from __future__ import annotations

import importlib.util
import re
import logging
import os
import threading
from typing import Any

import cv2
import numpy as np

from ocr_core.base import Availability, OcrUnavailableError, RawLine
from ocr_core.selection import choose_hypothesis
from shared_types import ModelInfo

log = logging.getLogger(__name__)

REC_MODELS = {
    "latin": "latin_PP-OCRv5_mobile_rec",
    "en": "en_PP-OCRv5_mobile_rec",
    "arabic": "arabic_PP-OCRv5_mobile_rec",
}
REC_LANGS = {"latin": ["fr", "en", "latin"], "en": ["en"], "arabic": ["ar"]}
ORIENTATION_MODEL = "PP-LCNet_x1_0_doc_ori"


def _crop_polygon(rgb: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Perspective-crop a (possibly rotated) quadrilateral text box."""
    pts = poly.astype("float32").reshape(4, 2)
    w = int(max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3])))
    h = int(max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))
    w, h = max(w, 2), max(h, 2)
    dst = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype="float32")
    m = cv2.getPerspectiveTransform(pts, dst)
    crop = cv2.warpPerspective(rgb, m, (w, h), borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_CUBIC)
    if h / w >= 1.5:  # vertical text box -> rotate so the recognizer sees a horizontal line
        crop = np.rot90(crop)
    return np.ascontiguousarray(crop)


class PaddleProvider:
    name = "paddleocr"

    def __init__(self, det_model: str = "PP-OCRv5_mobile_det", device: str = "cpu", use_orientation: bool = True, rec_batch_size: int = 8):
        self.det_model = det_model
        self.device = device
        self.use_orientation = use_orientation
        self.rec_batch_size = rec_batch_size
        self._lock = threading.Lock()
        # Paddle predictors are not thread-safe (concurrent run() corrupts shared tensors:
        # "Tensor holds no memory"). All inference on one provider instance is serialised.
        self._infer_lock = threading.RLock()
        self._det: Any = None
        self._rec: dict[str, Any] = {}
        self._ori: Any = None
        self._ori_failed = False

    # -- availability -------------------------------------------------------------------
    def availability(self) -> Availability:
        if importlib.util.find_spec("paddleocr") is None or importlib.util.find_spec("paddle") is None:
            return Availability(False, "paddleocr/paddlepaddle not installed")
        return Availability(True)

    def version(self) -> str | None:
        try:
            import paddleocr

            return paddleocr.__version__
        except Exception:  # pragma: no cover
            return None

    def models(self) -> list[ModelInfo]:
        v = self.version()
        infos = [ModelInfo(provider=self.name, task="detection", name=self.det_model, version=v, device=self.device)]
        for key, model in REC_MODELS.items():
            infos.append(ModelInfo(provider=self.name, task="recognition", name=model, version=v, languages=REC_LANGS[key], device=self.device))
        if self.use_orientation:
            infos.append(ModelInfo(provider=self.name, task="orientation", name=ORIENTATION_MODEL, version=v, device=self.device))
        return infos

    # -- lazy loading ---------------------------------------------------------------------
    def _ensure(self, keys: set[str]) -> None:
        av = self.availability()
        if not av.available:
            raise OcrUnavailableError(av.reason or "paddle unavailable")
        os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
        with self._lock:
            from paddleocr import TextDetection, TextRecognition

            if self._det is None:
                log.info("loading paddle detection model %s on %s", self.det_model, self.device)
                self._det = TextDetection(model_name=self.det_model, device=self.device)
            for k in keys:
                if k not in self._rec:
                    log.info("loading paddle recognition model %s", REC_MODELS[k])
                    self._rec[k] = TextRecognition(model_name=REC_MODELS[k], device=self.device)

    def warmup(self, scripts: set[str] | None = None) -> None:
        self._ensure(scripts or {"latin", "arabic"})

    # -- inference ----------------------------------------------------------------------
    def detect_orientation(self, rgb: np.ndarray) -> tuple[int, float] | None:
        if not self.use_orientation or self._ori_failed:
            return None
        try:
            with self._lock:
                if self._ori is None:
                    from paddleocr import DocImgOrientationClassification

                    self._ori = DocImgOrientationClassification(model_name=ORIENTATION_MODEL, device=self.device)
            with self._infer_lock:
                res = self._ori.predict(rgb[:, :, ::-1].copy(), batch_size=1)[0]
            label = str(res["label_names"][0])
            score = float(res["scores"][0])
            # the classifier reports how far the page is rotated counter-clockwise;
            # correcting requires rotating it back clockwise by the same amount
            deg = int(label)
            return ((360 - deg) % 360 if deg else 0), score
        except Exception as exc:  # model download failure etc. – record, don't fake
            log.warning("orientation model unavailable: %s", exc)
            self._ori_failed = True
            return None

    def recognize(self, rgb: np.ndarray, scripts: set[str]) -> list[RawLine]:
        keys = {k for k in scripts if k in REC_MODELS} or {"latin", "arabic"}
        self._ensure(keys)
        with self._infer_lock:
            return self._recognize(rgb, keys)

    def _recognize(self, rgb: np.ndarray, keys: set[str]) -> list[RawLine]:
        bgr = rgb[:, :, ::-1].copy()  # paddle expects BGR ndarray
        det = self._det.predict(bgr, batch_size=1)[0]
        polys = [np.asarray(p, dtype=float) for p in det["dt_polys"]]
        det_scores = [float(s) for s in det["dt_scores"]]
        if not polys:
            return []
        crops = [_crop_polygon(bgr, p) for p in polys]
        hyps: dict[str, list[tuple[str, float]]] = {}
        for k in sorted(keys):
            results = self._rec[k].predict(crops, batch_size=self.rec_batch_size)
            hyps[k] = [(str(r["rec_text"]), float(r["rec_score"])) for r in results]
        lines: list[RawLine] = []
        for i, poly in enumerate(polys):
            per = {k: hyps[k][i] for k in hyps}
            key, text, score, flags = choose_hypothesis(per)
            alts = [{"model": REC_MODELS[k], "text": t, "score": round(s, 4)} for k, (t, s) in per.items() if k != key]
            if key == "arabic" and "latin" in self._rec and _DIGIT.search(per.get("latin", ("", 0))[0]):
                repaired = self._repair_digits(crops[i], text)
                if repaired and repaired != text:
                    alts.append({"model": REC_MODELS["arabic"], "text": text, "score": round(score, 4), "note": "before digit repair"})
                    text = repaired
                    flags = [f for f in flags if f != "digits_possibly_dropped"] + ["digits_repaired_by_segmentation"]
            lines.append(
                RawLine(
                    polygon=poly.tolist(),
                    text=text,
                    score=max(0.0, min(1.0, score)),
                    det_score=det_scores[i] if i < len(det_scores) else None,
                    model=REC_MODELS[key],
                    alternatives=alts,
                    flags=flags,
                )
            )
        return lines

    def _repair_digits(self, crop: np.ndarray, arabic_text: str) -> str | None:
        """The Arabic recognizer tends to drop Western digit runs inside Arabic lines
        (measured on PP-OCRv5 arabic rec). Split the line at word gaps, re-read each segment
        with both recognizers and take digit-only segments from the Latin model. Returns None
        if the line cannot be segmented or the repair would lose Arabic text."""
        segs = _segment_words(crop)
        if len(segs) < 2:
            return None
        lat = self._rec["latin"].predict(segs, batch_size=self.rec_batch_size)
        ara = self._rec["arabic"].predict(segs, batch_size=self.rec_batch_size)
        parts: list[str] = []
        for seg_l, seg_a in zip(reversed(lat), reversed(ara)):  # RTL: rightmost segment first
            lt, ls = str(seg_l["rec_text"]).strip(), float(seg_l["rec_score"])
            at = str(seg_a["rec_text"]).strip()
            if _DIGITS_ONLY.fullmatch(lt) and ls >= 0.85 and not _ARABIC_LETTER.search(at):
                parts.append(lt)
            elif _DIGIT.search(at):
                # digits glued to Arabic letters: neither model is reliable here -> keep the
                # original line and its "digits_possibly_dropped" flag rather than guess
                return None
            elif at:
                parts.append(at)
        repaired = " ".join(parts)
        before = len(_ARABIC_LETTER.findall(arabic_text))
        after = len(_ARABIC_LETTER.findall(repaired))
        if after < 0.8 * before or not _DIGIT.search(repaired):
            return None
        return repaired


_DIGIT = re.compile(r"\d")
_DIGITS_ONLY = re.compile(r"[\d][\d\s.,/\-+()]*")
_ARABIC_LETTER = re.compile(r"[ء-يٱ-ۓ]")


def _segment_words(crop: np.ndarray) -> list[np.ndarray]:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h = bw.shape[0]
    ink = (bw > 0).sum(axis=0) > max(1, int(0.03 * h))
    min_gap = max(3, int(0.3 * h))
    segs: list[tuple[int, int]] = []
    start = None
    gap = 0
    for x, on in enumerate(ink):
        if on:
            if start is None:
                start = x
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                segs.append((start, x - gap + 1))
                start, gap = None, 0
    if start is not None:
        segs.append((start, len(ink)))
    pad = max(2, h // 8)
    return [np.ascontiguousarray(crop[:, max(0, a - pad) : min(crop.shape[1], b + pad)]) for a, b in segs if b - a > 2]
