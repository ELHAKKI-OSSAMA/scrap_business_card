"""QR detection/decoding with OpenCV. Decoded content is untrusted data: it is displayed raw,
URLs are validated but never opened, and nothing is imported without user action."""

from __future__ import annotations

import re
import cv2
import numpy as np

from shared_types import BBox, QrCode, Side
from validation.contact import is_safe_url

def _parse_vcard(raw: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in raw.replace("\r\n ", "").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        base = key.split(";")[0].upper()
        if base in {"FN", "N", "ORG", "TITLE", "TEL", "EMAIL", "URL", "ADR", "NOTE"}:
            out.setdefault(base.lower(), []).append(value.strip())
    return out


def _parse_mecard(raw: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    body = raw[len("MECARD:") :]
    for part in re.split(r"(?<!\\);", body):
        if ":" in part:
            k, v = part.split(":", 1)
            out.setdefault(k.lower(), []).append(v.replace("\\;", ";"))
    return out


def classify_qr(raw: str) -> tuple[str, dict]:
    s = raw.strip()
    upper = s.upper()
    if upper.startswith("BEGIN:VCARD"):
        return "vcard", _parse_vcard(s)
    if upper.startswith("MECARD:"):
        return "mecard", _parse_mecard(s)
    if upper.startswith("MAILTO:"):
        return "email", {"email": [s[7:]]}
    if upper.startswith("TEL:"):
        return "tel", {"tel": [s[4:]]}
    if upper.startswith("WIFI:"):
        return "wifi", {}
    if re.match(r"^https?://", s, re.IGNORECASE):
        return "url", {"url": [s]}
    return "text", {}


def decode_qr_codes(rgb: np.ndarray, side: Side) -> list[QrCode]:
    detector = cv2.QRCodeDetector()
    bgr = rgb[:, :, ::-1]
    try:
        ok, decoded, points, _ = detector.detectAndDecodeMulti(bgr)
    except cv2.error:
        return []
    if not ok:
        return []
    out: list[QrCode] = []
    for i, raw in enumerate(decoded):
        if not raw:
            continue
        kind, parsed = classify_qr(raw)
        pts = np.asarray(points[i]).reshape(-1, 2)
        x0, y0 = pts.min(axis=0)
        x1, y1 = pts.max(axis=0)
        out.append(
            QrCode(
                id=f"{side.value[0]}-qr{i}",
                side=side,
                raw=raw,
                kind=kind,  # type: ignore[arg-type]
                parsed=parsed,
                url_is_safe=is_safe_url(raw) if kind == "url" else None,
                bbox=BBox(x=float(x0), y=float(y0), w=float(x1 - x0), h=float(y1 - y0)),
            )
        )
    return out
