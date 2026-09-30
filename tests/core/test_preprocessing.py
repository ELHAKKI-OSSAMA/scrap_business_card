from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from document_preprocessing import (
    ImageValidationError,
    assess_quality,
    detect_document_quad,
    estimate_skew_angle,
    preprocess,
    rotate_bound,
    validate_image_bytes,
)
from ml_helpers import render_line


def _encode(img: Image.Image, fmt="JPEG", **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def test_rejects_non_images_and_mismatch():
    with pytest.raises(ImageValidationError) as e:
        validate_image_bytes(b"GIF89a" + b"0" * 100)
    assert e.value.code == "unsupported_type"
    with pytest.raises(ImageValidationError) as e:
        validate_image_bytes(b"")
    assert e.value.code == "empty_file"


def test_decompression_bomb_rejected():
    img = Image.new("L", (9000, 9000))
    data = _encode(img, "PNG")
    with pytest.raises(ImageValidationError):
        validate_image_bytes(data, max_pixels=20_000_000)


def test_exif_orientation_applied():
    img = Image.new("RGB", (400, 200), "white")
    exif = img.getexif()
    exif[0x0112] = 6  # rotate 90 CW on display
    v = validate_image_bytes(_encode(img, exif=exif.tobytes()))
    assert v.exif_transposed and (v.width, v.height) == (200, 400)


def test_quality_flags():
    dark = np.full((600, 900, 3), 20, np.uint8)
    q = assess_quality(dark)
    assert q.is_dark and "dark" in q.warnings
    small = np.full((200, 300, 3), 255, np.uint8)
    assert assess_quality(small).is_low_resolution


def test_perspective_boundary_detection():
    card = np.full((500, 800, 3), 250, np.uint8)
    canvas = np.full((900, 1300, 3), 60, np.uint8)
    canvas[200:700, 250:1050] = card
    quad = detect_document_quad(canvas)
    assert quad is not None
    xs, ys = quad[:, 0], quad[:, 1]
    assert abs(xs.min() - 250) < 15 and abs(ys.min() - 200) < 15 and abs(xs.max() - 1050) < 15


def test_no_warp_when_card_fills_frame():
    assert detect_document_quad(np.full((500, 800, 3), 250, np.uint8)) is None


def test_deskew_estimate():
    base = np.vstack([render_line("Chère Maman, il fait très beau ici") for _ in range(4)])
    rotated = rotate_bound(base, 5.0)
    angle = estimate_skew_angle(rotated)
    assert abs(angle + 5.0) < 1.5 or abs(angle - 5.0) < 1.5  # magnitude recovered
    res = preprocess(rotated)
    assert any(s.name == "deskew" and s.applied for s in res.steps)
