"""Upload validation: size limits, real file-type sniffing (not the client's MIME claim),
decompression-bomb protection and EXIF orientation."""

from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}
_PIL_FORMAT_TO_MIME = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "TIFF": "image/tiff"}


class ImageValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def sniff_mime(data: bytes) -> str | None:
    head = data[:16]
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    return None


@dataclass
class ValidatedImage:
    mime: str
    width: int
    height: int
    sha256: str
    size_bytes: int
    exif_transposed: bool
    rgb: np.ndarray  # H x W x 3, RGB, EXIF orientation applied


def validate_image_bytes(data: bytes, *, max_bytes: int = 15 * 1024 * 1024, max_pixels: int = 60_000_000) -> ValidatedImage:
    if not data:
        raise ImageValidationError("empty_file", "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise ImageValidationError("file_too_large", f"File exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    mime = sniff_mime(data)
    if mime not in ALLOWED_MIME_TYPES:
        raise ImageValidationError("unsupported_type", "Only JPEG, PNG, WEBP and TIFF images are accepted.")
    Image.MAX_IMAGE_PIXELS = max_pixels
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as probe:
                probe.verify()
            img = Image.open(io.BytesIO(data))
            fmt_mime = _PIL_FORMAT_TO_MIME.get(img.format or "")
            if fmt_mime != mime:
                raise ImageValidationError("type_mismatch", "File content does not match an allowed image format.")
            if img.width * img.height > max_pixels:
                raise ImageValidationError("image_too_large", "Image dimensions exceed the pixel limit.")
            if min(img.width, img.height) < 32:
                raise ImageValidationError("image_too_small", "Image is too small to contain readable text.")
            orientation = img.getexif().get(0x0112, 1)
            img = ImageOps.exif_transpose(img)
            rgb = np.asarray(img.convert("RGB"))
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ImageValidationError("corrupt_image", "The image could not be decoded.") from exc
    return ValidatedImage(
        mime=mime,
        width=int(rgb.shape[1]),
        height=int(rgb.shape[0]),
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        exif_transposed=orientation not in (None, 1),
        rgb=rgb,
    )
