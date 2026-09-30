"""Runs the real business-card pipeline (OcrEngine + extract_business_card, as the worker does)
on the synthetic fixtures and prints what was extracted. Diagnostic tool, not a test.

    python tests/business_card/harness.py [case_key ...] [--save DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fixtures import build_all, to_rgb  # noqa: E402
from ocr_core import OcrEngine  # noqa: E402
from ocr_core.paddle_provider import PaddleProvider  # noqa: E402
from extraction import extract_business_card  # noqa: E402
from shared_types import Side  # noqa: E402

_ENGINE: OcrEngine | None = None


def engine() -> OcrEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = OcrEngine(PaddleProvider())
    return _ENGINE


def run_case(case, default_region: str | None = None):
    pages, images, timings = [], {}, {}
    t0 = time.perf_counter()
    for side, img in case.images.items():
        page, processed = engine().process_page(to_rgb(img), Side(side))
        pages.append(page)
        images[Side(side)] = processed
    t1 = time.perf_counter()
    ex, regions = extract_business_card(pages, images, default_region=default_region)
    t2 = time.perf_counter()
    timings = {"ocr_and_preprocess_s": round(t1 - t0, 3), "extract_s": round(t2 - t1, 4), "ocr_ms_by_page": [p.processing_ms for p in pages]}
    return pages, ex, regions, timings


def summary(ex) -> dict:
    d = ex.model_dump(mode="json")
    v = lambda k: (d.get(k) or {}).get("value")  # noqa: E731
    return {
        "full_name": v("full_name"), "arabic_name": v("arabic_name"), "job_title": v("job_title"), "company": v("company"),
        "specialty": v("specialty"), "industry": v("industry"), "website": v("website"), "linkedin": v("linkedin"),
        "phones": [(p["original"], p["e164"], p["type"], p["region_inferred_from"]) for p in d["phones"]],
        "emails": [e["value"] for e in d["emails"]],
        "address": {k: d["address"].get(k) for k in ("original_text", "street", "postal_code", "city", "country")} if d.get("address") else None,
        "qr": [(q["kind"], q["parsed"]) for q in d["qr_codes"]], "qr_checks": [(c["field"], c["status"], c["qr_value"], c["ocr_value"]) for c in d.get("qr_checks") or []], "review_fields": d.get("review_fields"), "description": v("professional_description"),
        "logo": bool(d.get("logo")), "languages": d.get("languages"), "warnings": d.get("warnings"),
        "qualifications": [q["value"] for q in d.get("qualifications") or []],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*")
    ap.add_argument("--save")
    a = ap.parse_args()
    for case in build_all():
        if a.keys and not any(case.key.startswith(k) for k in a.keys):
            continue
        if a.save:
            for side, img in case.images.items():
                Path(a.save).mkdir(parents=True, exist_ok=True)
                img.save(Path(a.save) / f"{case.key}-{side}.png")
        pages, ex, _, t = run_case(case)
        print(f"\n=== {case.key}: {case.description}  {t}")
        print("OCR:", [l.text for p in pages for l in p.lines])
        print(json.dumps(summary(ex), ensure_ascii=False, indent=None))


if __name__ == "__main__":
    main()
