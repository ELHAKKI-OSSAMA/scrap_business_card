"""HTTP workflow check against a running stack (default: the Docker gateway on :8080).

    python tests/integration/workflows.py [--base http://localhost:8080/api/v1]

Uses real OCR (whatever provider the stack runs) on SYNTHETIC samples from
ml/datasets/synthetic/out and compares against their ground-truth annotations. It prints what
matched and what did not; it never substitutes expected values for OCR output.
Exit code 0 only if every hard check passes (API contract, not OCR accuracy).
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
SYNTH = ROOT / "ml" / "datasets" / "synthetic" / "out"
failures: list[str] = []


def check(cond: bool, label: str) -> None:
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        failures.append(label)


def note(label: str) -> None:
    print("  INFO  " + label)


def val(fv):
    return fv.get("value") if isinstance(fv, dict) else None


def run_job(c: httpx.Client, route: str, doc_id: str) -> dict:
    r = c.post(f"/{route}/{doc_id}/process")
    check(r.status_code == 202, f"{route}: process accepted (202), got {r.status_code}")
    job_id = r.json()["job_id"]
    for _ in range(120):
        j = c.get(f"/jobs/{job_id}").json()
        if j["status"] in ("completed", "failed"):
            break
        time.sleep(1)
    check(j["status"] == "completed", f"{route}: job completed (status={j['status']}, error={j.get('error_code')})")
    return c.get(f"/{route}/{doc_id}").json()


def pick(prefix: str, need_back: bool) -> Path:
    for d in sorted(SYNTH.glob(prefix)):
        if (d / "front.jpg").exists() and (not need_back or (d / "back.jpg").exists()):
            return d
    raise SystemExit(f"no synthetic sample matching {prefix} (run ml/datasets/synthetic/generate.py)")


def business_card(c: httpx.Client) -> None:
    print("\nBUSINESS CARD")
    sample = pick("bc-fr-*-clean", need_back=False)
    truth = json.loads((sample / "annotation.json").read_text(encoding="utf-8"))
    note(f"sample {sample.name} (synthetic)")
    doc = c.post("/business-cards", json={"title": "wf card"}).json()
    r = c.post(f"/business-cards/{doc['id']}/images", params={"side": "front"}, files={"file": ("front.jpg", (sample / "front.jpg").read_bytes(), "image/jpeg")})
    check(r.status_code == 200, f"upload front ({r.status_code})")
    doc = run_job(c, "business-cards", doc["id"])
    data = doc.get("data") or {}
    gt = truth.get("fields", truth)
    for k in ("full_name", "job_title", "company", "website"):
        exp = gt.get(k) if isinstance(gt, dict) else None
        if isinstance(exp, dict):
            exp = exp.get("value")
        note(f"{k}: got={val(data.get(k))!r} expected={exp!r}")
    phones, emails = data.get("phones") or [], data.get("emails") or []
    note(f"phones: {[(p.get('original'), p.get('e164'), p.get('valid')) for p in phones]}")
    note(f"emails: {[(e.get('value'), e.get('valid')) for e in emails]}")
    check(bool(phones) and all(p.get("e164", "").startswith("+") for p in phones if p.get("e164")), "phones parsed; E.164 normalised where valid")
    check(bool(emails), "email extracted")
    # server-side validation rejects a malformed email correction
    bad = c.patch(f"/business-cards/{doc['id']}/fields", json={"changes": [{"path": "emails", "op": "append", "value": "not-an-email"}]})
    check(bad.status_code == 422, f"invalid email correction rejected (422), got {bad.status_code}")
    r = c.patch(f"/business-cards/{doc['id']}/fields", json={"changes": [{"path": "job_title", "value": "Directrice"}], "expected_version": doc["version"]})
    check(r.status_code == 200, f"edit job title ({r.status_code})")
    vcf = c.get(f"/business-cards/{doc['id']}/export", params={"format": "vcf"})
    check(vcf.status_code == 200 and vcf.text.startswith("BEGIN:VCARD") and "Directrice" in vcf.text, "vCard export contains the correction")
    dups = c.get(f"/business-cards/{doc['id']}/duplicates")
    check(dups.status_code == 200, "duplicate suggestions endpoint (suggest only)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8080/api/v1")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base, timeout=120)
    email = f"wf-{secrets.token_hex(4)}@example.com"
    r = c.post("/auth/register", json={"email": email, "password": secrets.token_urlsafe(18), "locale": "fr"})
    check(r.status_code == 201, f"register throwaway account ({r.status_code})")
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    models = c.get("/models").json()
    print("\nMODELS\n  " + json.dumps(models, ensure_ascii=False)[:1500])
    hw = json.dumps(models).lower()
    check("handwriting" in hw, "models endpoint reports handwriting capability status")
    business_card(c)
    print(f"\n{'OK' if not failures else 'FAILED'}: {len(failures)} hard check(s) failed" + ("".join(f"\n  - {f}" for f in failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
