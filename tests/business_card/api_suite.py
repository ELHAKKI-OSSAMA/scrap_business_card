"""Business Card suite against a RUNNING stack (default: Docker gateway :8080).

    python tests/business_card/api_suite.py [--base http://localhost:8080/api/v1] [--out FILE]

For every SYNTHETIC fixture: create → upload (front/back) → process (real OCR in the worker) →
retrieve → compare with ground truth → verify a field → edit a field → export JSON/CSV/vCard.
Then security probes. Prints PASS/FAIL per hard check and INFO for accuracy observations;
never substitutes expected values for OCR output. Exit 0 only if all hard checks pass.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import io
import json
import secrets
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fixtures import build_all  # noqa: E402

failures: list[str] = []
results: list[dict] = []


def check(cond: bool, label: str) -> bool:
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        failures.append(label)
    return cond


def info(label: str) -> None:
    print("  INFO  " + label)


def png(img) -> bytes:
    b = io.BytesIO()
    img.convert("RGB").save(b, format="PNG")
    return b.getvalue()


def account(base: str) -> httpx.Client:
    c = httpx.Client(base_url=base, timeout=180)
    r = c.post("/auth/register", json={"email": f"bc-{secrets.token_hex(4)}@example.com", "password": secrets.token_urlsafe(18), "locale": "fr"})
    r.raise_for_status()
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    return c


def wait_job(c: httpx.Client, job_id: str) -> dict:
    for _ in range(300):
        j = c.get(f"/jobs/{job_id}").json()
        if j["status"] in ("completed", "failed"):
            return j
        time.sleep(0.5)
    return j


def v(d: dict, k: str):
    return (d.get(k) or {}).get("value")


def run_case(c: httpx.Client, case) -> str:
    print(f"\n[{case.key}] {case.description}")
    t0 = time.perf_counter()
    doc = c.post("/business-cards", json={"title": case.key, "client_ref": f"{case.key}-{secrets.token_hex(3)}"}).json()
    for side, img in case.images.items():
        r = c.post(f"/business-cards/{doc['id']}/images", params={"side": side}, files={"file": (f"{side}.png", png(img), "image/png")})
        check(r.status_code == 200, f"upload {side} ({r.status_code})")
    r = c.post(f"/business-cards/{doc['id']}/process")
    check(r.status_code == 202, f"process accepted ({r.status_code})")
    job = wait_job(c, r.json()["job_id"])
    e2e = time.perf_counter() - t0
    check(job["status"] == "completed", f"job completed ({job['status']} {job.get('error_code')})")
    check(job.get("provider") == "paddleocr", f"provider recorded: {job.get('provider')}")
    got = c.get(f"/business-cards/{doc['id']}").json()
    d = got["data"] or {}
    lines = [l for p in got.get("ocr") or [] for l in p["lines"]]
    check(bool(lines) and all(l.get("bbox") for l in lines), f"OCR lines with boxes saved ({len(lines)})")
    check({p["side"] for p in got["ocr"]} == set(case.images), "every uploaded side processed")
    t = case.truth
    for k in ("full_name", "arabic_name", "job_title", "company"):
        if k in t:
            check(v(d, k) == t[k], f"{k}: {v(d, k)!r} (expected {t[k]!r})")
    if "phones_e164" in t:
        check(set(t["phones_e164"]) <= {p["e164"] for p in d["phones"]}, f"phones {[p['e164'] for p in d['phones']]}")
    if "emails" in t:
        check([e["value"] for e in d["emails"]] == t["emails"], f"emails {[e['value'] for e in d['emails']]}")
    # evidence on each extracted field
    for k in ("full_name", "company", "job_title"):
        f = d.get(k) or {}
        if f.get("value") and not str(f.get("notes") or "").startswith("inferred"):
            check(bool(f.get("source_region_ids")) and f.get("confidence") is not None and f.get("original_value"), f"{k} keeps source/confidence/original")
    info(f"review_fields={d.get('review_fields')} warnings={d.get('warnings')}")
    # review: verify a field, edit another, retrieve
    if v(d, "full_name"):
        r = c.patch(f"/business-cards/{doc['id']}/fields", json={"changes": [{"path": "full_name", "op": "verify"}], "expected_version": got["version"]})
        check(r.status_code == 200 and r.json()["data"]["full_name"]["review_status"] == "verified", "verify full_name")
        got = r.json()
    r = c.patch(f"/business-cards/{doc['id']}/fields", json={"changes": [{"path": "department", "value": "Direction (édité)"}], "expected_version": got["version"]})
    check(r.status_code == 200, f"edit department ({r.status_code})")
    again = c.get(f"/business-cards/{doc['id']}").json()
    check(v(again["data"], "department") == "Direction (édité)", "edit persisted on retrieval")
    check([l["text"] for p in again["ocr"] for l in p["lines"]] == [l["text"] for l in lines], "raw OCR unchanged after edits")
    # exports
    js = c.get(f"/business-cards/{doc['id']}/export", params={"format": "json"})
    csvr = c.get(f"/business-cards/{doc['id']}/export", params={"format": "csv"})
    vcf = c.get(f"/business-cards/{doc['id']}/export", params={"format": "vcf"})
    check(js.status_code == 200 and json.loads(js.text), "JSON export")
    check(csvr.status_code == 200 and csvr.text.startswith("﻿") and "Direction (édité)" in csvr.text, "CSV export (UTF-8 BOM, edit included)")
    body = vcf.text
    check(vcf.status_code == 200 and body.startswith("BEGIN:VCARD\r\nVERSION:3.0") and body.rstrip().endswith("END:VCARD") and "\nFN:" in body, "vCard 3.0 structure")
    if v(d, "arabic_name"):
        check(v(d, "arabic_name") in body.replace("\r\n ", ""), "Arabic preserved in vCard")
    if str((d.get("job_title") or {}).get("notes") or "").startswith("inferred"):
        check("TITLE:" not in body, "inferred title not exported to vCard")
    results.append({"case": case.key, "e2e_s": round(e2e, 2), "job_processing_ms": job.get("processing_ms"), "fields": {k: v(d, k) for k in ("full_name", "arabic_name", "job_title", "company", "specialty")},
                    "phones": [(p["original"], p["e164"], p["region_inferred_from"]) for p in d["phones"]], "emails": [e["value"] for e in d["emails"]],
                    "qr_checks": d.get("qr_checks"), "review_fields": d.get("review_fields")})
    return doc["id"]


def security(base: str, c: httpx.Client, doc_id: str) -> None:
    print("\n[security]")
    anon = httpx.Client(base_url=base, timeout=30)
    check(anon.get("/business-cards").status_code == 401, "list requires authentication")
    check(anon.get(f"/business-cards/{doc_id}/images/front").status_code == 401, "images are not public")
    other = account(base)
    check(other.get(f"/business-cards/{doc_id}").status_code == 404, "other workspace: document 404")
    check(other.get(f"/business-cards/{doc_id}/images/front").status_code == 404, "other workspace: image 404")
    check(other.get(f"/business-cards/{doc_id}/export", params={"format": "vcf"}).status_code == 404, "other workspace: export 404")
    check(len(other.get("/business-cards", params={"q": "' OR 1=1 --"}).json().get("items", [])) == 0, "SQL-injection-like search returns nothing from other workspaces")
    d2 = c.post("/business-cards", json={}).json()
    r = c.post(f"/business-cards/{d2['id']}/images", params={"side": "front"}, files={"file": ("x.png", b"<?php echo 1; ?>", "image/png")})
    check(r.status_code in (400, 415, 422), f"non-image rejected ({r.status_code})")
    r = c.post(f"/business-cards/{d2['id']}/images", params={"side": "../../etc/passwd"}, files={"file": ("x.png", b"\x89PNG", "image/png")})
    check(r.status_code == 422, f"path-traversal side rejected ({r.status_code})")
    check(c.get("/business-cards/..%2F..%2Fetc%2Fpasswd").status_code in (404, 422), "path traversal in id rejected")
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (16 * 1024 * 1024)
    r = c.post(f"/business-cards/{d2['id']}/images", params={"side": "front"}, files={"file": ("big.png", big, "image/png")})
    check(r.status_code == 413, f"oversize upload rejected ({r.status_code})")
    r = c.patch(f"/business-cards/{doc_id}/fields", json={"changes": [{"path": "company", "value": "=HYPERLINK(\"http://evil\")"}]})
    check(r.status_code == 200, "formula-like value can be stored")
    csvt = c.get(f"/business-cards/{doc_id}/export", params={"format": "csv"}).text
    check("'=HYPERLINK" in csvt, "CSV formula injection neutralised")
    r = c.patch(f"/business-cards/{doc_id}/fields", json={"changes": [{"path": "website", "value": "javascript:alert(1)"}]})
    check(r.status_code == 422, f"javascript: URL rejected as website ({r.status_code})")
    r = c.patch(f"/business-cards/{doc_id}/fields", json={"changes": [{"path": "emails", "op": "append", "value": "<script>@x"}]})
    check(r.status_code == 422, f"invalid e-mail rejected ({r.status_code})")


def batch(c: httpx.Client, cases) -> None:
    print("\n[batch: 10 cards submitted together]")
    ids = []
    for case in cases[:10]:
        doc = c.post("/business-cards", json={"title": "batch-" + case.key}).json()
        for side, img in case.images.items():
            c.post(f"/business-cards/{doc['id']}/images", params={"side": side}, files={"file": ("f.png", png(img), "image/png")})
        ids.append(doc["id"])
    t0 = time.perf_counter()
    jobs = [c.post(f"/business-cards/{i}/process").json()["job_id"] for i in ids]
    with cf.ThreadPoolExecutor(10) as ex:
        done = list(ex.map(lambda j: wait_job(c, j), jobs))
    wall = time.perf_counter() - t0
    check(all(j["status"] == "completed" for j in done), f"10/10 batch jobs completed ({sum(j['status'] == 'completed' for j in done)})")
    ms = sorted(j.get("processing_ms") or 0 for j in done)
    info(f"batch wall {wall:.1f}s, per-job processing_ms p50={ms[len(ms) // 2]} max={ms[-1]}, throughput {10 / wall * 60:.1f} cards/min (1 worker, concurrency 1)")
    results.append({"batch10": {"wall_s": round(wall, 2), "processing_ms": ms}})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8080/api/v1")
    ap.add_argument("--out", default="ml/evaluation/reports/business-card-api-suite.json")
    a = ap.parse_args()
    c = account(a.base)
    ready = httpx.get(a.base + "/health/ready", timeout=30).json()
    check(ready.get("status") == "ready", f"stack ready: {ready.get('checks')}")
    cases = build_all()
    last = None
    for case in cases:
        last = run_case(c, case)
    security(a.base, c, last)
    batch(c, [x for x in cases if len(x.images) == 1])
    Path(a.out).write_text(json.dumps({"source": "synthetic fixtures", "base": a.base, "failures": failures, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'OK' if not failures else 'FAILED'}: {len(failures)} hard check(s) failed" + "".join(f"\n  - {f}" for f in failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
