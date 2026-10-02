"""Evaluation runner: OCR (CER/WER, detection P/R), extraction (exact match, entity P/R/F1),
confidence calibration and system metrics (latency, memory), broken down by product,
language, script, image quality and text type.

    python ml/evaluation/evaluate.py --data ml/datasets/synthetic/out --provider paddleocr

The dataset's ``source`` ("synthetic" / "real") is carried into every report; synthetic and
real results are never merged. Annotation format: docs/models/evaluation.md.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

from document_preprocessing import validate_image_bytes  # noqa: E402
from extraction import extract_business_card  # noqa: E402
from language_detection import normalize_search  # noqa: E402
from ocr_core import OcrEngine, OcrSettings, get_provider  # noqa: E402
from shared_types import Side  # noqa: E402
from validation.postal import COUNTRY_NAMES  # noqa: E402


def levenshtein(a, b) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    return levenshtein(ref, hyp) / max(1, len(ref))


def _match_lines(gt_lines: list[dict], pred: list[str]) -> list[tuple[dict, str | None, int]]:
    """Greedy one-to-one line matching by edit distance. Returns (gt, pred_text|None, distance)."""
    pairs = []
    for gi, g in enumerate(gt_lines):
        for pi, p in enumerate(pred):
            pairs.append((cer(g["text"], p), gi, pi))
    pairs.sort()
    used_g, used_p, out = set(), set(), {}
    for c, gi, pi in pairs:
        if gi in used_g or pi in used_p or c > 0.6:
            continue
        used_g.add(gi)
        used_p.add(pi)
        out[gi] = pi
    res = []
    for gi, g in enumerate(gt_lines):
        if gi in out:
            p = pred[out[gi]]
            res.append((g, p, levenshtein(g["text"], p)))
        else:
            res.append((g, None, len(g["text"])))
    return res, len(pred) - len(used_p)


class Agg:
    def __init__(self):
        self.d = defaultdict(lambda: defaultdict(float))

    def add(self, key: str, **vals):
        for k, v in vals.items():
            self.d[key][k] += v

    def table(self):
        return {k: dict(v) for k, v in sorted(self.d.items())}


def _v(fv) -> str | None:
    if fv is None:
        return None
    v = fv.get("value") if isinstance(fv, dict) else fv
    return None if v in (None, "") else str(v)


def _eq(a, b) -> bool:
    return a is not None and b is not None and normalize_search(str(a)) == normalize_search(str(b))


def _country_iso(text: str | None) -> str | None:
    if not text:
        return None
    return COUNTRY_NAMES.get(normalize_search(text)) or next((iso for name, iso in COUNTRY_NAMES.items() if normalize_search(name) == normalize_search(text)), None)


def _vision_client():
    """Ollama vision client from the environment / .env (OLLAMA_KEYS, OLLAMA_MODEL, OLLAMA_BASE_URL)."""
    from extraction import OllamaVisionClient

    env = dict(os.environ)
    dot = Path(".env")
    if dot.exists():
        for line in dot.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    keys = [k.strip() for k in env.get("OLLAMA_KEYS", "").split(",") if k.strip()]
    return OllamaVisionClient(model=env.get("OLLAMA_MODEL", "gemma4:31b"), api_keys=keys, base_url=env.get("OLLAMA_BASE_URL", "https://ollama.com"))


def evaluate(data_dir: Path, provider: str, limit: int | None, languages: list[str] | None, vision: bool = False) -> dict:
    try:
        import psutil

        proc = psutil.Process()
    except ImportError:  # pragma: no cover
        proc = None
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    source = manifest.get("source", "unknown")
    sample_ids = manifest["samples"][:limit] if limit else manifest["samples"]
    t_load = time.perf_counter()
    if provider == "ollama":  # cloud-only mode (Vercel): Gemma reads the card and extracts the fields
        from extraction import OllamaCloudEngine

        engine = OllamaCloudEngine(_vision_client())
    else:
        engine = OcrEngine(get_provider(OcrSettings(provider=provider, fallback=None)))
    ocr_agg, det_agg, field_agg, ent_agg = Agg(), Agg(), Agg(), Agg()
    calib = defaultdict(lambda: [0, 0])  # bucket -> [n, correct]
    latencies: list[float] = []
    failures = []
    peak_rss = 0
    models = None
    vclient = _vision_client() if vision else None
    vision_latencies: list[float] = []
    for sid in sample_ids:
        ann = json.loads((data_dir / sid / "annotation.json").read_text(encoding="utf-8"))
        tags = ann.get("tags", [])
        quality = next((t.split(":")[1] for t in tags if t.startswith("quality:")), "unknown")
        text_type = "printed"
        lang_tag = ann.get("languages", "und")
        pages, images, raw_images = [], {}, []
        try:
            for side, sd in ann["sides"].items():
                raw = (data_dir / sd["image"]).read_bytes()
                raw_images.append(raw)
                v = validate_image_bytes(raw)
                t0 = time.perf_counter()
                page, img = engine.process_page(v.rgb, Side(side), languages=languages, exif_transposed=v.exif_transposed)
                latencies.append(time.perf_counter() - t0)
                pages.append(page)
                images[Side(side)] = img
                models = models or [m.model_dump() for m in page.models]
                pred_texts = [l.text for l in page.lines if l.text.strip()]
                matched, unmatched_pred = _match_lines(sd["lines"], pred_texts)
                for g, p, dist in matched:
                    lang = g.get("language", "und")
                    key_sets = [f"lang={lang}", f"script={g['script']}", f"quality={quality}", f"type={text_type}", f"product={ann['product']}", "ALL"]
                    words_ref = g["text"].split()
                    words_hyp = (p or "").split()
                    for key in key_sets:
                        ocr_agg.add(key, chars=len(g["text"]), char_errors=dist, words=len(words_ref), word_errors=levenshtein(words_ref, words_hyp), lines=1, exact=int(p == g["text"]))
                        det_agg.add(key, gt_lines=1, detected=int(p is not None))
                det_agg.add("ALL", pred_lines=len(pred_texts), unmatched_pred=unmatched_pred)
                if proc:
                    peak_rss = max(peak_rss, proc.memory_info().rss)
        except Exception as exc:  # noqa: BLE001
            failures.append({"id": sid, "error": f"{type(exc).__name__}: {exc}"[:300]})
            continue

        gt = ann["fields"]
        group = f"{ann['product']}|lang={lang_tag}|quality={quality}|type={text_type}"
        if ann["product"] == "business_card":
            ex, _ = extract_business_card(pages, images)
            if provider == "ollama":
                from extraction import merge_vision

                for card in engine.cards.values():
                    ex = merge_vision(ex, card, [l for pg in pages for l in pg.lines], model=engine.provider.model)
                engine.cards.clear()
            if vclient:
                from extraction import vision_enrich

                t0 = time.perf_counter()
                ex = vision_enrich(ex, raw_images, [l for pg in pages for l in pg.lines], vclient)
                vision_latencies.append(time.perf_counter() - t0)
                if "llm_unavailable_fallback_rules" in ex.warnings:
                    failures.append({"id": sid, "error": "vision_llm_unavailable"})
            d = ex.model_dump(mode="json")
            checks = {
                "full_name": (gt.get("full_name"), _v(d["full_name"])),
                "first_name": (gt.get("first_name"), _v(d["first_name"])),
                "last_name": (gt.get("last_name"), _v(d["last_name"])),
                "arabic_name": (gt.get("arabic_name"), _v(d["arabic_name"])),
                "job_title": (gt.get("job_title"), _v(d["job_title"])),
                "company": (gt.get("company"), _v(d["company"])),
                "website": (gt.get("website"), _v(d["website"])),
                "industry": (gt.get("industry"), _v(d["industry"])),
                "address.postal_code": ((gt.get("address") or {}).get("postal_code"), (d.get("address") or {}).get("postal_code")),
                "address.city": ((gt.get("address") or {}).get("city"), (d.get("address") or {}).get("city")),
                "address.country": ((gt.get("address") or {}).get("country_iso"), _country_iso((d.get("address") or {}).get("country"))),
            }
            conf_of = {k: (d[k]["confidence"] if isinstance(d.get(k), dict) else None) for k in checks}
            # entities
            gt_emails = {e.lower() for e in gt.get("emails", [])}
            pr_emails = {str(e["value"]).lower() for e in d["emails"] if e.get("value")}
            gt_phones = set(gt.get("phones", []))
            pr_phones = {p["e164"] for p in d["phones"] if p.get("e164")}
            for name, g_set, p_set in (("email", gt_emails, pr_emails), ("phone", gt_phones, pr_phones)):
                for key in (f"{name}|ALL", f"{name}|lang={lang_tag}", f"{name}|quality={quality}"):
                    ent_agg.add(key, tp=len(g_set & p_set), fp=len(p_set - g_set), fn=len(g_set - p_set))
            ptypes = gt.get("phone_types", {})
            for p in d["phones"]:
                if p.get("e164") in ptypes:
                    field_agg.add("phone_type|ALL", n=1, correct=int(p["type"] == ptypes[p["e164"]]))
        for fname, (g, p) in checks.items():
            if g in (None, ""):
                continue
            ok = _eq(g, p)
            for key in (f"{fname}|ALL", f"{fname}|{group}"):
                field_agg.add(key, n=1, correct=int(ok), missing=int(p is None))
            c = conf_of.get(fname)
            if c is not None:
                b = min(9, int(c * 10))
                calib[b][0] += 1
                calib[b][1] += int(ok)

    def rates(tbl, num, den, name):
        return {k: {**v, name: round(v[num] / v[den], 4) if v.get(den) else None} for k, v in tbl.items()}

    ocr = rates(ocr_agg.table(), "char_errors", "chars", "CER")
    ocr = {k: {**v, "WER": round(v["word_errors"] / v["words"], 4) if v.get("words") else None, "line_accuracy": round(v["exact"] / v["lines"], 4) if v.get("lines") else None} for k, v in ocr.items()}
    det = det_agg.table()
    for k, v in det.items():
        v["recall"] = round(v["detected"] / v["gt_lines"], 4) if v.get("gt_lines") else None
    if "ALL" in det and det["ALL"].get("pred_lines"):
        det["ALL"]["precision"] = round((det["ALL"]["pred_lines"] - det["ALL"]["unmatched_pred"]) / det["ALL"]["pred_lines"], 4)
    fields = {}
    for k, v in field_agg.table().items():
        if "n" in v:
            fields[k] = {**v, "exact_match": round(v["correct"] / v["n"], 4)}
        else:
            fields[k] = {**v, "CER": round(v["char_errors"] / v["chars"], 4) if v.get("chars") else None}
    ents = {}
    for k, v in ent_agg.table().items():
        p = v["tp"] / (v["tp"] + v["fp"]) if (v["tp"] + v["fp"]) else None
        r = v["tp"] / (v["tp"] + v["fn"]) if (v["tp"] + v["fn"]) else None
        f1 = 2 * p * r / (p + r) if p and r else None
        ents[k] = {**v, "precision": round(p, 4) if p is not None else None, "recall": round(r, 4) if r is not None else None, "f1": round(f1, 4) if f1 is not None else None}
    calibration = [{"bucket": f"{b / 10:.1f}-{(b + 1) / 10:.1f}", "n": n, "accuracy": round(c / n, 3)} for b, (n, c) in sorted(calib.items())]
    return {
        "source": source,
        "banner": "SYNTHETIC DATA ONLY – not representative of real-world accuracy" if source == "synthetic" else "REAL annotated data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider + ("+vision:" + vclient.model if vclient else ""),
        "vision_latency_s_mean": round(statistics.mean(vision_latencies), 3) if vision_latencies else None,
        "languages_restriction": languages,
        "models": models,
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "cpu_count": os.cpu_count()},
        "samples": len(sample_ids),
        "failures": failures,
        "ocr": ocr,
        "detection": det,
        "fields": fields,
        "entities": ents,
        "confidence_calibration": calibration,
        "system": {
            "model_load_plus_run_s": round(time.perf_counter() - t_load, 1),
            "images": len(latencies),
            "latency_s_mean": round(statistics.mean(latencies), 3) if latencies else None,
            "latency_s_p50": round(statistics.median(latencies), 3) if latencies else None,
            "latency_s_p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 3) if latencies else None,
            "throughput_img_per_min": round(60 / statistics.mean(latencies), 1) if latencies else None,
            "peak_rss_mb": round(peak_rss / 1e6) if peak_rss else None,
            "failure_rate": round(len(failures) / max(1, len(sample_ids)), 4),
        },
    }


def to_markdown(r: dict) -> str:
    out = [f"# Evaluation report – {r['provider']}", "", f"> **{r['banner']}**", "", f"Generated {r['generated_at']} · samples: {r['samples']} · failures: {len(r['failures'])}", ""]
    out += ["## OCR (line level)", "", "| Group | Lines | CER | WER | Line accuracy |", "|---|---:|---:|---:|---:|"]
    for k, v in r["ocr"].items():
        out.append(f"| {k} | {int(v['lines'])} | {v['CER']} | {v['WER']} | {v['line_accuracy']} |")
    d = r["detection"].get("ALL", {})
    out += ["", f"Detection recall (GT lines matched at CER ≤ 0.6): **{d.get('recall')}**, precision: **{d.get('precision')}**", ""]
    out += ["## Extraction – exact match per field", "", "| Field / group | N | Exact match | Missing |", "|---|---:|---:|---:|"]
    for k, v in r["fields"].items():
        if "exact_match" in v and k.endswith("|ALL"):
            out.append(f"| {k[:-4]} | {int(v['n'])} | {v['exact_match']} | {int(v.get('missing', 0))} |")
    out += ["", "## Entities (P / R / F1)", "", "| Entity | P | R | F1 |", "|---|---:|---:|---:|"]
    for k, v in r["entities"].items():
        out.append(f"| {k} | {v['precision']} | {v['recall']} | {v['f1']} |")
    out += ["", "## Confidence calibration (field confidence vs. exact match)", "", "| Confidence | N | Accuracy |", "|---|---:|---:|"]
    for c in r["confidence_calibration"]:
        out.append(f"| {c['bucket']} | {c['n']} | {c['accuracy']} |")
    s = r["system"]
    out += ["", "## System", "", f"- images: {s['images']}, mean latency {s['latency_s_mean']} s (p50 {s['latency_s_p50']}, p95 {s['latency_s_p95']}), throughput ≈ {s['throughput_img_per_min']} img/min (single process, {r['environment']['cpu_count']} logical CPUs)",
            f"- peak RSS: {s['peak_rss_mb']} MB · failure rate: {s['failure_rate']}", f"- environment: {r['environment']['platform']}, Python {r['environment']['python']}", ""]
    out += ["## Per-group field detail", "", "| Field | Group | N | Exact |", "|---|---|---:|---:|"]
    for k, v in r["fields"].items():
        if "exact_match" in v and not k.endswith("|ALL") and "|" in k:
            f, g = k.split("|", 1)
            out.append(f"| {f} | {g} | {int(v['n'])} | {v['exact_match']} |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="ml/datasets/synthetic/out")
    ap.add_argument("--provider", default="paddleocr", choices=["paddleocr", "tesseract", "ollama"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--languages", help="comma list to restrict recognizers, e.g. ar,fr")
    ap.add_argument("--out", default="ml/evaluation/reports")
    ap.add_argument("--vision", action="store_true", help="apply the Ollama vision LLM after the rules (sends images to OLLAMA_BASE_URL)")
    args = ap.parse_args()
    rep = evaluate(Path(args.data), args.provider, args.limit, args.languages.split(",") if args.languages else None, vision=args.vision)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{rep['source']}-{args.provider}" + ("-vision" if args.vision else "")
    (out / f"{stem}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / f"{stem}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


if __name__ == "__main__":
    main()
