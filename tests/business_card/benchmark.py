"""Business-card processing benchmark on SYNTHETIC fixtures (in-process, CPU).

    python tests/business_card/benchmark.py [--out reports/business-card-benchmark.json]

Stages timed:
  preprocessing  = document_preprocessing.preprocess() alone (same function the engine calls)
  ocr            = OcrEngine.process_page() total minus the preprocessing time (derived)
  extraction     = extract_business_card()
Memory: process RSS (psutil). GPU: not measured (CPU PaddlePaddle build).
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fixtures import build_all, to_rgb  # noqa: E402
from harness import engine  # noqa: E402
from document_preprocessing import preprocess  # noqa: E402
from extraction import extract_business_card  # noqa: E402
from shared_types import Side  # noqa: E402


def one(case) -> dict:
    eng = engine()
    pre_s = ocr_total = 0.0
    pages, images = [], {}
    for side, img in case.images.items():
        rgb = to_rgb(img)
        t0 = time.perf_counter()
        preprocess(rgb, eng.preprocess_options)
        t1 = time.perf_counter()
        page, processed = eng.process_page(rgb, Side(side))
        t2 = time.perf_counter()
        pre_s += t1 - t0
        ocr_total += t2 - t1
        pages.append(page)
        images[Side(side)] = processed
    t3 = time.perf_counter()
    extract_business_card(pages, images)
    ext = time.perf_counter() - t3
    return {"case": case.key, "images": len(case.images), "preprocessing_s": pre_s, "ocr_s": max(ocr_total - pre_s, 0.0), "extraction_s": ext, "total_s": ocr_total + ext}


def stats(rows: list[dict], key: str) -> dict:
    xs = [r[key] for r in rows]
    xs_sorted = sorted(xs)
    return {"mean": round(statistics.mean(xs), 3), "p50": round(statistics.median(xs), 3), "p95": round(xs_sorted[min(len(xs) - 1, int(0.95 * len(xs)))], 3), "max": round(max(xs), 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ml/evaluation/reports/business-card-benchmark.json")
    a = ap.parse_args()
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    cases = build_all()
    t = time.perf_counter()
    engine()  # model load
    load_s = time.perf_counter() - t
    rss_loaded = proc.memory_info().rss
    warm = one(cases[1])  # first inference includes lazy init; reported separately
    single = one(cases[1])
    ten_cases = [c for c in cases if len(c.images) == 1][:10]
    t = time.perf_counter()
    ten = [one(c) for c in ten_cases]
    ten_wall = time.perf_counter() - t
    t = time.perf_counter()
    all_rows = [one(c) for c in cases]
    all_wall = time.perf_counter() - t
    peak = proc.memory_info().peak_wset if hasattr(proc.memory_info(), "peak_wset") else proc.memory_info().rss
    report = {
        "source": "synthetic", "banner": "SYNTHETIC fixtures; CPU; not representative of real photos",
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "cpu_count": psutil.cpu_count(), "device": "cpu"},
        "model_load_s": round(load_s, 2), "first_inference_s": round(warm["total_s"], 3),
        "single_image": {k: round(v, 3) if isinstance(v, float) else v for k, v in single.items()},
        "ten_images_sequential": {"wall_s": round(ten_wall, 2), "throughput_img_per_min": round(10 / ten_wall * 60, 1),
                                  **{k: stats(ten, k) for k in ("preprocessing_s", "ocr_s", "extraction_s", "total_s")}},
        "all_fixtures": {"cards": len(all_rows), "images": sum(r["images"] for r in all_rows), "wall_s": round(all_wall, 2),
                         **{k: stats(all_rows, k) for k in ("preprocessing_s", "ocr_s", "extraction_s", "total_s")}},
        "memory_mb": {"before_load": round(rss0 / 2**20), "after_model_load": round(rss_loaded / 2**20), "peak": round(peak / 2**20)},
        "gpu_memory": "not measured (CPU build)",
        "per_card": [{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()} for r in all_rows],
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_card"}, indent=2))


if __name__ == "__main__":
    main()
