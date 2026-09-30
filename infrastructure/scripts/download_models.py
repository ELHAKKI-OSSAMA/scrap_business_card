"""Pre-fetch every OCR model the suite uses into PADDLE_PDX_CACHE_HOME (baked into the Docker
image so containers start offline and deterministically), then print what was installed.

    PADDLE_PDX_CACHE_HOME=/opt/models python infrastructure/scripts/download_models.py
"""

from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")


def main() -> int:
    from ocr_core.paddle_provider import ORIENTATION_MODEL, REC_MODELS, PaddleProvider

    det = os.environ.get("OCR_DET_MODEL", "PP-OCRv5_mobile_det")
    p = PaddleProvider(det_model=det, device="cpu", use_orientation=True)
    p.warmup(set(REC_MODELS))
    import numpy as np

    if p.detect_orientation(np.full((64, 64, 3), 255, np.uint8)) is None:
        print(f"WARNING: orientation model {ORIENTATION_MODEL} could not be loaded", file=sys.stderr)
    print(json.dumps([m.model_dump() for m in p.models()], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
