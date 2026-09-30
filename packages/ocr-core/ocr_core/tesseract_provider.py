"""Tesseract 5 adapter (baseline / fallback). Requires the ``tesseract`` binary and the
``ara``, ``fra`` and ``eng`` traineddata packages (installed in the Docker image)."""

from __future__ import annotations

import importlib.util
import shutil
from collections import defaultdict

import numpy as np

from ocr_core.base import Availability, OcrUnavailableError, RawLine
from shared_types import ModelInfo

_LANG_FOR_SCRIPT = {"latin": ["fra", "eng"], "en": ["eng"], "arabic": ["ara"]}


class TesseractProvider:
    name = "tesseract"

    def __init__(self, psm: int = 11):
        self.psm = psm  # 11 = sparse text: suits cards with scattered blocks

    def _installed_langs(self) -> set[str]:
        import pytesseract

        return set(pytesseract.get_languages(config=""))

    def availability(self) -> Availability:
        if importlib.util.find_spec("pytesseract") is None:
            return Availability(False, "pytesseract not installed")
        if shutil.which("tesseract") is None:
            return Availability(False, "tesseract binary not found on PATH")
        try:
            missing = {"ara", "fra", "eng"} - self._installed_langs()
        except Exception as exc:  # pragma: no cover
            return Availability(False, f"tesseract not usable: {exc}")
        if missing:
            return Availability(False, f"missing traineddata: {sorted(missing)}")
        return Availability(True)

    def version(self) -> str | None:
        try:
            import pytesseract

            return str(pytesseract.get_tesseract_version())
        except Exception:
            return None

    def models(self) -> list[ModelInfo]:
        v = self.version()
        return [
            ModelInfo(provider=self.name, task="recognition", name="tesseract-lstm:ara+fra+eng", version=v, languages=["ar", "fr", "en"], device="cpu")
        ]

    def detect_orientation(self, rgb: np.ndarray) -> tuple[int, float] | None:
        return None  # OSD needs the osd traineddata; not relied upon

    def recognize(self, rgb: np.ndarray, scripts: set[str]) -> list[RawLine]:
        av = self.availability()
        if not av.available:
            raise OcrUnavailableError(av.reason or "tesseract unavailable")
        import pytesseract

        langs: list[str] = []
        for s in sorted(scripts) or ["latin", "arabic"]:
            for lang in _LANG_FOR_SCRIPT.get(s, []):
                if lang not in langs:
                    langs.append(lang)
        data = pytesseract.image_to_data(rgb, lang="+".join(langs), config=f"--oem 1 --psm {self.psm}", output_type=pytesseract.Output.DICT)
        groups: dict[tuple[int, int, int], list[int]] = defaultdict(list)
        for i, word in enumerate(data["text"]):
            if word and word.strip() and float(data["conf"][i]) >= 0:
                groups[(data["block_num"][i], data["par_num"][i], data["line_num"][i])].append(i)
        lines: list[RawLine] = []
        for idx in groups.values():
            x0 = min(data["left"][i] for i in idx)
            y0 = min(data["top"][i] for i in idx)
            x1 = max(data["left"][i] + data["width"][i] for i in idx)
            y1 = max(data["top"][i] + data["height"][i] for i in idx)
            words = sorted(idx, key=lambda i: data["left"][i])
            text = " ".join(data["text"][i] for i in words)
            # Tesseract returns Arabic words in logical order but lines sorted LTR by position
            from language_detection import detect_script
            from shared_types import Script

            if detect_script(text) == Script.arabic:
                text = " ".join(data["text"][i] for i in reversed(words))
            conf = float(np.mean([float(data["conf"][i]) for i in idx])) / 100
            lines.append(RawLine(polygon=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], text=text, score=round(conf, 4), model=f"tesseract:{'+'.join(langs)}"))
        return lines
