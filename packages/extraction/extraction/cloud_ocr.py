"""Cloud-only OCR (``OCR_PROVIDER=ollama``): Gemma 4 through the Ollama API reads the card.

One request per card side returns the printed lines with their boxes **and** the structured
fields. The lines become a normal ``OcrPage`` (so review, search, layout rules and the region
overlay keep working); the fields are merged afterwards by :func:`extraction.merge_vision`, which
only accepts values found in those lines.

Needs only Pillow + NumPy (no OpenCV, no Paddle): this is the engine used on Vercel.

Honest limits: the model gives no per-line confidence (``confidence=None``) and its boxes are
approximate; there is no preprocessing (deskew/denoise) and no QR decoding in this mode.
"""

from __future__ import annotations

import io
import json
import re
import time

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from extraction.vision_llm import PROMPT as FIELDS_PROMPT
from extraction.vision_llm import OllamaVisionClient, VisionCard
from language_detection import detect_line_language, direction_for, normalize_display
from ocr_core.reading_order import assign_reading_order
from shared_types import BBox, ModelInfo, OcrLine, OcrPage, PreprocessingStep, Side

MAX_SIDE = 1600

READ_PROMPT = """Read this business card photo.
1. "lines": every printed text line, top to bottom, the left column before the right column. Copy the
   text exactly (keep Arabic in Arabic script, keep accents, no translation, no correction). "box" is
   [x0, y0, x1, y1] normalised to 0-1000 relative to the whole image width and height.
2. "card": the contact fields, following these rules:
""" + FIELDS_PROMPT.split("Rules:", 1)[1].split("Answer with", 1)[0] + """
Answer with ONE JSON object and nothing else:
{"lines": [{"text": str, "box": [x0, y0, x1, y1]}],
 "card": {"full_name": str|null, "first_name": str|null, "last_name": str|null, "job_title": str|null,
          "company": str|null, "department": str|null, "emails": [str], "website": str|null,
          "phones": [{"type": "mobile"|"phone"|"fax"|"whatsapp"|"unknown", "number": str}],
          "address": {"street": str|null, "building": str|null, "postal_code": str|null, "city": str|null,
                      "region": str|null, "country": str|null} | null}}"""


class _Line(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    box: list[float] | None = Field(default=None, min_length=4, max_length=4)


class CloudRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lines: list[_Line]
    card: VisionCard


_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def parse_cloud_read(raw: str) -> tuple[CloudRead, list[str]]:
    """Parse the model answer. Shape deviations that cannot inject data are repaired and reported
    (unknown keys dropped, malformed boxes replaced); anything else raises ValueError."""
    m = _FENCE.match(raw)
    payload = json.loads(m.group(1) if m else raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("lines"), list):
        raise ValueError("answer has no 'lines' list")
    notes: list[str] = []
    lines = []
    for item in payload["lines"]:
        if isinstance(item, str):
            item = {"text": item}
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            notes.append("cloud_ocr:line_dropped")
            continue
        box = item.get("box")
        if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
            box = None
            notes.append("cloud_ocr:box_missing")
        lines.append({"text": item["text"], "box": box})
    card = payload.get("card") if isinstance(payload.get("card"), dict) else {}
    extra = sorted(set(card) - set(VisionCard.model_fields))
    if extra:
        notes.append("cloud_ocr:ignored_keys:" + ",".join(extra)[:80])
    card = {k: v for k, v in card.items() if k in VisionCard.model_fields}
    if isinstance(card.get("phones"), list):
        kinds = {"mobile", "phone", "fax", "whatsapp", "unknown"}
        card["phones"] = [
            {"type": p.get("type") if p.get("type") in kinds else "unknown", "number": p["number"]}
            for p in card["phones"]
            if isinstance(p, dict) and isinstance(p.get("number"), str)
        ]
    if isinstance(card.get("emails"), list):
        card["emails"] = [e for e in card["emails"] if isinstance(e, str)]
    if isinstance(card.get("address"), dict):
        card["address"] = {k: v for k, v in card["address"].items() if k in ("street", "building", "postal_code", "city", "region", "country")}
    return CloudRead.model_validate({"lines": lines, "card": card}), notes


def _downscale(rgb: np.ndarray) -> Image.Image:
    img = Image.fromarray(rgb)
    scale = MAX_SIDE / max(img.size)
    if scale < 1:
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return img


class _ProviderInfo:
    def __init__(self, model: str):
        self.name = "ollama"
        self.model = model

    def models(self) -> list[ModelInfo]:
        return [ModelInfo(provider="ollama", task="recognition+extraction", name=self.model)]


class OllamaCloudEngine:
    """Same call shape as ``ocr_core.OcrEngine.process_page``; the parsed fields of every side are
    kept in ``cards`` for the job to merge after the rule-based extraction."""

    def __init__(self, client: OllamaVisionClient):
        self.client = client
        self.provider = _ProviderInfo(client.model)
        self.cards: dict[Side, VisionCard] = {}

    def process_page(self, rgb: np.ndarray, side: Side, *, languages: list[str] | None = None, exif_transposed: bool = False) -> tuple[OcrPage, np.ndarray]:
        t0 = time.perf_counter()
        img = _downscale(rgb)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        try:
            read, notes = parse_cloud_read(self.client.chat(READ_PROMPT, [buf.getvalue()]))
        except ValueError:  # malformed answer: ask once more before failing the job
            read, notes = parse_cloud_read(self.client.chat(READ_PROMPT, [buf.getvalue()]))
            notes.append("cloud_ocr:retried")
        self.cards[side] = read.card
        w, h = img.size
        prefix = side.value[0]
        lines: list[OcrLine] = []
        for i, l in enumerate(x for x in read.lines if x.text.strip()):
            box = l.box or [0, 1000 * i / max(1, len(read.lines)), 1000, 1000 * (i + 1) / max(1, len(read.lines))]  # stacked fallback
            x0, y0, x1, y1 = (max(0.0, min(1000.0, v)) for v in box)
            x0, x1 = sorted((x0, x1))
            y0, y1 = sorted((y0, y1))
            bx, by, bw, bh = x0 * w / 1000, y0 * h / 1000, max(1.0, (x1 - x0) * w / 1000), max(1.0, (y1 - y0) * h / 1000)
            guess = detect_line_language(l.text)
            lines.append(OcrLine(
                id=f"{prefix}-{i}", side=side, text=l.text, normalized_text=normalize_display(l.text),
                bbox=BBox(x=bx, y=by, w=bw, h=bh),
                polygon=[[round(bx, 1), round(by, 1)], [round(bx + bw, 1), round(by, 1)], [round(bx + bw, 1), round(by + bh, 1)], [round(bx, 1), round(by + bh, 1)]],
                confidence=None, script=guess.script, language=guess.language, language_confidence=guess.confidence,
                direction=direction_for(guess.script, l.text), model=self.client.model,
            ))
        lines = assign_reading_order(lines)
        steps = [PreprocessingStep(name="resize", applied=img.size != (rgb.shape[1], rgb.shape[0]), details={"max_side": MAX_SIDE, "exif_transposed": exif_transposed})]
        if notes:
            steps.append(PreprocessingStep(name="cloud_ocr_answer_repairs", applied=True, details={"notes": notes}))
        page = OcrPage(side=side, width=w, height=h, lines=lines, preprocessing=steps, models=self.provider.models(), processing_ms=int((time.perf_counter() - t0) * 1000))
        return page, np.asarray(img)
