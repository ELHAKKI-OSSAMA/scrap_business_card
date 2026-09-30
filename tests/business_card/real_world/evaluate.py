"""Real-world business-card evaluation against a hand-verified ground truth.

    python tests/business_card/real_world/evaluate.py <card_dir_name> [--api] [--base URL] [--root DIR]

* Uses the production pipeline unchanged: OcrEngine(PaddleProvider()) + extract_business_card
  (the calls made by the worker). Nothing from the ground truth is given to the pipeline.
* Refuses to report results as "validated" unless ground_truth.json exists and has "verified_by".
* Writes out/raw_ocr.json, out/extraction.json, out/report.json, out/report.md.
* --api: uploads the same images to the running stack, applies corrections for every wrong field
  FROM THE GROUND TRUTH through the review API, and checks retrieval + JSON/CSV/vCard exports.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import secrets
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


# ---------------------------------------------------------------- metrics

def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def nfc(s: str | None) -> str:
    return unicodedata.normalize("NFC", s or "").strip()


def cer(ref: str, hyp: str) -> float:
    ref, hyp = nfc(ref), nfc(hyp)
    return levenshtein(ref, hyp) / max(len(ref), 1)


def char_diff(ref: str, hyp: str) -> list[dict]:
    """Position-by-position comparison (after alignment by edit operations)."""
    ref, hyp = nfc(ref), nfc(hyp)
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]))
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            ops.append({"ref": ref[i - 1], "ocr": hyp[j - 1], "op": "ok" if ref[i - 1] == hyp[j - 1] else "substituted"})
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append({"ref": ref[i - 1], "ocr": None, "op": "missing"})
            i -= 1
        else:
            ops.append({"ref": None, "ocr": hyp[j - 1], "op": "extra"})
            j -= 1
    return ops[::-1]


# ---------------------------------------------------------------- pipeline (unchanged production calls)

def load_images(card_dir: Path) -> dict[str, np.ndarray]:
    out = {}
    for side in ("front", "back"):
        for ext in IMAGE_EXT:
            p = card_dir / f"{side}{ext}"
            if p.exists():
                out[side] = p
                break
    return out


def run_pipeline(paths: dict[str, Path]):
    from document_preprocessing import validate_image_bytes
    from extraction import extract_business_card
    from ocr_core import OcrEngine
    from ocr_core.paddle_provider import PaddleProvider
    from shared_types import Side

    eng = OcrEngine(PaddleProvider())
    pages, images, timing = [], {}, {}
    for side, p in paths.items():
        v = validate_image_bytes(p.read_bytes(), max_bytes=15 * 1024 * 1024, max_pixels=60_000_000)  # same validation as upload
        t0 = time.perf_counter()
        page, processed = eng.process_page(v.rgb, Side(side), exif_transposed=v.exif_transposed)
        timing[side] = round(time.perf_counter() - t0, 3)
        pages.append(page)
        images[Side(side)] = processed
    t0 = time.perf_counter()
    ex, regions = extract_business_card(pages, images, default_region=None)
    timing["extraction"] = round(time.perf_counter() - t0, 4)
    return pages, ex, regions, images, timing


# ---------------------------------------------------------------- comparison

def status_of(expected, got_field: dict | None, *, inferred_ok: bool = False) -> dict:
    got = (got_field or {}).get("value") if isinstance(got_field, dict) else got_field
    notes = str((got_field or {}).get("notes") or "") if isinstance(got_field, dict) else ""
    review = (got_field or {}).get("review_status") if isinstance(got_field, dict) else None
    inferred = notes.startswith("inferred")
    if expected in (None, "", []) and got in (None, "", []):
        st = "correct_absent"
    elif expected in (None, "", []):
        st = "inferred" if inferred else "hallucinated"
    elif got in (None, "", []):
        st = "missing"
    elif nfc(str(got)) == nfc(str(expected)):
        st = "correct"
    else:
        st = "incorrect"
    return {"expected": expected, "extracted": got, "status": st, "cer": round(cer(str(expected), str(got)), 4) if expected and got else None,
            "review_status": review, "inferred": inferred, "confidence": (got_field or {}).get("confidence") if isinstance(got_field, dict) else None,
            "original_value": (got_field or {}).get("original_value") if isinstance(got_field, dict) else None,
            "normalized_value": (got_field or {}).get("normalized_value") if isinstance(got_field, dict) else None,
            "source_region_ids": (got_field or {}).get("source_region_ids") if isinstance(got_field, dict) else None}


def compare(gt: dict, d: dict, raw_lines: list[dict]) -> dict:
    f = gt["fields"]
    res: dict[str, dict] = {}
    res["full_name"] = status_of(f.get("full_name"), d.get("full_name"))
    hon = None
    if str((d.get("full_name") or {}).get("notes") or "").startswith("honorific:"):
        hon = d["full_name"]["notes"].split(":", 1)[1].strip()
    res["honorific"] = status_of(f.get("honorific"), hon)
    res["arabic_name"] = status_of(f.get("arabic_name"), d.get("arabic_name"))
    res["job_title"] = status_of(f.get("job_title_printed"), d.get("job_title"))
    res["company (vs French clinic name)"] = status_of(f.get("clinic_name_fr"), d.get("company"))
    res["specialty"] = status_of(f.get("specialty_printed"), d.get("specialty"))
    res["professional_description"] = status_of(f.get("professional_description"), d.get("professional_description"))
    got_q = sorted(nfc(q.get("value")) for q in d.get("qualifications") or [])
    exp_q = sorted(nfc(q) for q in f.get("qualifications") or [])
    res["qualifications"] = {"expected": exp_q, "extracted": got_q, "status": "correct" if got_q == exp_q else ("missing" if not got_q else "incorrect"),
                             "missing": sorted(set(exp_q) - set(got_q)), "not_on_card": sorted(set(got_q) - set(exp_q))}
    got_e = [nfc(e.get("value")) for e in d.get("emails") or []]
    res["emails"] = {"expected": f.get("emails") or [], "extracted": got_e, "status": "correct" if got_e == [nfc(x) for x in f.get("emails") or []] else "incorrect"}
    res["website"] = status_of(f.get("website"), d.get("website"))
    addr = d.get("address") or {}
    res["address (raw OCR line)"] = status_of(f.get("address_line"), addr.get("original_text"))
    for k in ("street", "building", "postal_code", "city", "country"):
        res[f"address.{k}"] = status_of(f.get(k), addr.get(k))

    # phones: character by character on the printed form
    phones = []
    got_p = [p.get("original") for p in d.get("phones") or []]
    for exp in f.get("phones") or []:
        best = min(got_p, key=lambda g: levenshtein(nfc(exp), nfc(g)), default=None)
        phones.append({"expected": exp, "extracted_original": best, "status": "correct" if best and nfc(best) == nfc(exp) else ("missing" if best is None else "incorrect"),
                       "cer": round(cer(exp, best), 4) if best else None, "chars": char_diff(exp, best or ""),
                       "e164": next((p.get("e164") for p in d.get("phones") or [] if p.get("original") == best), None),
                       "region_inferred_from": next((p.get("region_inferred_from") for p in d.get("phones") or [] if p.get("original") == best), None)})
    extra_p = [g for g in got_p if g not in [p["extracted_original"] for p in phones]]
    res["phones"] = {"items": phones, "not_on_card": extra_p}

    # Arabic clinic name: retained in raw OCR? represented in a field?
    ar = nfc(f.get("clinic_name_ar"))
    if ar:
        best_line = min(raw_lines, key=lambda l: levenshtein(ar, nfc(l["text"])), default=None)
        in_field = [k for k, val in d.items() if isinstance(val, dict) and nfc(str(val.get("value") or "")) == ar]
        res["clinic_name_ar"] = {"expected": ar, "closest_raw_ocr_line": best_line and best_line["text"], "raw_line_id": best_line and best_line["id"],
                                 "cer_raw": round(cer(ar, best_line["text"]), 4) if best_line else None, "retained_verbatim_in_raw_ocr": bool(best_line) and nfc(best_line["text"]) == ar,
                                 "represented_in_a_field": in_field or None,
                                 "separate_from_french_clinic_name": bool(in_field) and "company" not in in_field}

    # Hassan II: raw OCR vs structured street, never silently corrected
    hl = [l for l in raw_lines if "hassan" in l["text"].lower()]
    res["hassan_ii_check"] = {"raw_ocr_lines": [l["text"] for l in hl], "raw_ocr_says_II": any("Hassan II" in l["text"] for l in hl),
                              "structured_street": addr.get("street"), "original_text_kept": addr.get("original_text"),
                              "correction_recorded_as_warning": "ocr_correction:roman_numeral_in_street" in (d.get("warnings") or [])}
    return res


def line_cer(gt_lines: list[dict], raw_lines: list[dict]) -> dict:
    per_line, agg = [], {}
    used: set[str] = set()
    for g in gt_lines:
        cands = [l for l in raw_lines if l["side"] == g.get("side", "front") and l["id"] not in used] or [l for l in raw_lines if l["id"] not in used]
        best = min(cands, key=lambda l: cer(g["text"], l["text"]), default=None)
        if best is not None and cer(g["text"], best["text"]) < 0.8:
            used.add(best["id"])
        else:
            best = None
        e = levenshtein(nfc(g["text"]), nfc(best["text"])) if best else len(nfc(g["text"]))
        per_line.append({"lang": g["lang"], "expected": g["text"], "ocr": best and best["text"], "ocr_id": best and best["id"], "errors": e, "chars": len(nfc(g["text"])),
                         "cer": round(e / max(len(nfc(g["text"])), 1), 4), "exact": bool(best) and nfc(best["text"]) == nfc(g["text"]), "detected": best is not None})
        a = agg.setdefault(g["lang"], {"lines": 0, "chars": 0, "errors": 0, "exact": 0, "undetected": 0})
        a["lines"] += 1
        a["chars"] += len(nfc(g["text"]))
        a["errors"] += e
        a["exact"] += per_line[-1]["exact"]
        a["undetected"] += best is None
    for a in agg.values():
        a["CER"] = round(a["errors"] / max(a["chars"], 1), 4)
        a["line_accuracy"] = round(a["exact"] / max(a["lines"], 1), 4)
    tot = {"chars": sum(a["chars"] for a in agg.values()), "errors": sum(a["errors"] for a in agg.values())}
    tot["CER"] = round(tot["errors"] / max(tot["chars"], 1), 4)
    extra = [l["text"] for l in raw_lines if l["id"] not in used]
    return {"per_line": per_line, "by_language": agg, "all": tot, "ocr_lines_not_in_ground_truth": extra}


# ---------------------------------------------------------------- API round trip

def api_round_trip(base: str, paths: dict[str, Path], gt: dict, fields_cmp: dict) -> dict:
    import httpx

    c = httpx.Client(base_url=base, timeout=180)
    r = c.post("/auth/register", json={"email": f"rw-{secrets.token_hex(4)}@example.com", "password": secrets.token_urlsafe(18), "locale": "fr"})
    r.raise_for_status()
    c.headers["Authorization"] = "Bearer " + r.json()["access_token"]
    doc = c.post("/business-cards", json={"title": "real-world medical card"}).json()
    for side, p in paths.items():
        r = c.post(f"/business-cards/{doc['id']}/images", params={"side": side}, files={"file": (p.name, p.read_bytes(), "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png")})
        r.raise_for_status()
    job_id = c.post(f"/business-cards/{doc['id']}/process").json()["job_id"]
    for _ in range(300):
        job = c.get(f"/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)
    got = c.get(f"/business-cards/{doc['id']}").json()
    f = gt["fields"]
    # corrections from the ground truth for every field that is wrong / missing / not on the card
    changes = []
    simple = {"full_name": "full_name", "arabic_name": "arabic_name", "specialty": "specialty_printed", "company": "clinic_name_fr", "professional_description": "professional_description", "website": "website"}
    for path, gk in simple.items():
        cur = (got["data"].get(path) or {}).get("value")
        if nfc(str(cur or "")) != nfc(str(f.get(gk) or "")):
            changes.append({"path": path, "value": f.get(gk)})
    if f.get("job_title_printed") is not None or (got["data"].get("job_title") or {}).get("value"):
        if nfc(str((got["data"].get("job_title") or {}).get("value") or "")) != nfc(str(f.get("job_title_printed") or "")):
            changes.append({"path": "job_title", "value": f.get("job_title_printed")})
    if got["data"].get("address") is not None:
        for k in ("street", "building", "postal_code", "city", "country"):
            if nfc(str(got["data"]["address"].get(k) or "")) != nfc(str(f.get(k) or "")):
                changes.append({"path": f"address.{k}", "value": f.get(k)})
    for i, p in reversed(list(enumerate(got["data"].get("phones") or []))):
        if nfc(p["original"]) not in [nfc(x) for x in f.get("phones") or []]:
            changes.append({"path": f"phones.{i}", "op": "remove"})
    have = [nfc(p["original"]) for p in got["data"].get("phones") or []]
    for x in f.get("phones") or []:
        if nfc(x) not in have:
            changes.append({"path": "phones", "op": "append", "value": {"original": x}})
    applied = None
    if changes:
        r = c.patch(f"/business-cards/{doc['id']}/fields", json={"changes": changes, "expected_version": got["version"]})
        applied = {"status": r.status_code, "changes": changes, "error": r.json().get("error") if r.status_code != 200 else None}
    after = c.get(f"/business-cards/{doc['id']}").json()
    exports = {fmt: c.get(f"/business-cards/{doc['id']}/export", params={"format": fmt}).text for fmt in ("json", "csv", "vcf")}
    checks = {}
    for path, gk in list(simple.items()) + [("job_title", "job_title_printed")]:
        exp = f.get(gk)
        now = (after["data"].get(path) or {}).get("value")
        checks[path] = {"expected": exp, "after_retrieval": now, "ok": nfc(str(now or "")) == nfc(str(exp or "")),
                        "in_json": exp is None or json.dumps(exp, ensure_ascii=False)[1:-1] in exports["json"] or json.dumps(exp)[1:-1] in exports["json"],
                        "in_csv": exp is None or nfc(exp) in nfc(exports["csv"]), "in_vcf": exp is None or nfc(exp) in nfc(exports["vcf"].replace("\r\n ", "").replace("\\,", ",").replace("\\;", ";"))}
    for x in f.get("phones") or []:
        checks[f"phone {x}"] = {"expected": x, "ok": nfc(x) in [nfc(p["original"]) for p in after["data"]["phones"]], "in_json": x in exports["json"], "in_csv": x in exports["csv"], "in_vcf": x in exports["vcf"]}
    raw_same = [l["text"] for p in got["ocr"] for l in p["lines"]] == [l["text"] for p in after["ocr"] for l in p["lines"]]
    history = c.get(f"/business-cards/{doc['id']}/history").json()
    return {"document_id": doc["id"], "job": {k: job.get(k) for k in ("status", "provider", "processing_ms", "error_code")}, "corrections": applied,
            "checks": checks, "raw_ocr_unchanged_after_corrections": raw_same, "history_events": len(history),
            "vcard": exports["vcf"], "csv": exports["csv"], "ui_url": base.replace("/api/v1", "") + f"/cards/documents/{doc['id']}"}


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("--root", default=str(HERE))
    ap.add_argument("--api", action="store_true")
    ap.add_argument("--base", default="http://localhost:8080/api/v1")
    a = ap.parse_args()
    card_dir = Path(a.root) / a.card
    paths = load_images(card_dir)
    if "front" not in paths:
        print(f"NO REAL PHOTO FOUND.\nPlace the photograph at:\n  {card_dir / 'front.jpg'}\n  (optional) {card_dir / 'back.jpg'}\nand the hand-verified annotation at:\n  {card_dir / 'ground_truth.json'}\n(template: {HERE / 'ground_truth.template.json'})")
        return 2
    gt_path = card_dir / "ground_truth.json"
    gt = json.loads(gt_path.read_text(encoding="utf-8")) if gt_path.exists() else None
    verified = bool(gt and gt.get("verified_by"))

    pages, ex, regions, images, timing = run_pipeline(paths)
    out = card_dir / "out"
    out.mkdir(exist_ok=True)
    raw_lines = [{"id": l.id, "side": l.side.value, "text": l.text, "confidence": l.confidence, "script": l.script.value, "language": l.language,
                  "direction": l.direction.value, "bbox": l.bbox.model_dump(), "model": l.model, "alternatives": l.alternatives} for p in pages for l in p.lines]
    d = ex.model_dump(mode="json")
    (out / "raw_ocr.json").write_text(json.dumps({"pages": [p.model_dump(mode="json") for p in pages], "lines": raw_lines}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "extraction.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    for side, img in images.items():
        Image.fromarray(img).save(out / f"processed-{side.value}.jpg", quality=90)

    report = {"card": a.card, "generated_at": datetime.now(timezone.utc).isoformat(), "images": {k: str(v.name) for k, v in paths.items()},
              "ground_truth": "verified" if verified else ("present but NOT verified" if gt else "MISSING"), "timing_s": timing,
              "models": [m.model_dump() for m in pages[0].models], "raw_ocr_transcription": [f"[{l['id']}] {l['text']}  (conf {l['confidence']:.3f}, {l['language']})" for l in raw_lines],
              "warnings": d.get("warnings"), "review_fields": d.get("review_fields")}
    if gt:
        report["line_cer"] = line_cer(gt.get("lines") or [], raw_lines)
        report["fields"] = compare(gt, d, raw_lines)
        scored = [v for k, v in report["fields"].items() if isinstance(v, dict) and v.get("status") in ("correct", "incorrect", "missing", "hallucinated", "correct_absent", "inferred")]
        with_gt = [v for v in scored if v["status"] in ("correct", "incorrect", "missing")]
        report["field_exact_match"] = {"fields_with_ground_truth": len(with_gt), "correct": sum(v["status"] == "correct" for v in with_gt),
                                       "accuracy": round(sum(v["status"] == "correct" for v in with_gt) / max(len(with_gt), 1), 4),
                                       "hallucinated": [k for k, v in report["fields"].items() if isinstance(v, dict) and v.get("status") == "hallucinated"],
                                       "inferred_not_printed": [k for k, v in report["fields"].items() if isinstance(v, dict) and v.get("status") == "inferred"]}
    if a.api:
        if not gt:
            print("--api needs ground_truth.json (corrections come from it)")
        else:
            report["api"] = api_round_trip(a.base, paths, gt, report.get("fields", {}))
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ground_truth", "timing_s", "raw_ocr_transcription")}, ensure_ascii=False, indent=2))
    if gt:
        print(json.dumps({"CER": report["line_cer"]["by_language"], "all": report["line_cer"]["all"], "field_exact_match": report["field_exact_match"]}, ensure_ascii=False, indent=2))
    if not verified:
        print("\nNOT VALIDATED: ground truth missing or not marked verified_by — results above are unverified.")
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
