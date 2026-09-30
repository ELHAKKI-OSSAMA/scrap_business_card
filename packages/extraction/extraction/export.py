"""Exports: vCard 3.0, CSV (spreadsheet-formula-injection safe) and JSON."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable


def _v(field: Any) -> str:
    if isinstance(field, dict):
        v = field.get("value")
        return "" if v is None else str(v)
    return "" if field is None else str(field)


def _printed(field: Any) -> str:
    """Value only if it was read from the card (or confirmed by a person), not merely inferred."""
    if isinstance(field, dict) and str(field.get("notes") or "").startswith("inferred") and field.get("review_status") not in ("verified", "corrected"):
        return ""
    return _v(field)


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def _fold(line: str) -> str:
    """RFC 6350 line folding at 75 octets (UTF-8 safe)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not parts else 74):
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def to_vcard(card: dict[str, Any]) -> str:
    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    # FN is mandatory in vCard 3.0: fall back to the Arabic name, then the company
    full = _v(card.get("full_name")) or _v(card.get("arabic_name")) or _v(card.get("company"))
    last, first = _v(card.get("last_name")), _v(card.get("first_name"))
    lines.append(f"N:{_esc(last)};{_esc(first)};;;")
    lines.append(f"FN:{_esc(full)}")
    if _v(card.get("arabic_name")) and _v(card.get("arabic_name")) != full:
        lines.append(f"X-PHONETIC-FULL-NAME;CHARSET=UTF-8:{_esc(_v(card.get('arabic_name')))}")
        lines.append(f"NICKNAME;CHARSET=UTF-8:{_esc(_v(card.get('arabic_name')))}")
    org = _v(card.get("company"))
    dept = _v(card.get("department"))
    if org or dept:
        lines.append(f"ORG:{_esc(org)}" + (f";{_esc(dept)}" if dept else ""))
    if _printed(card.get("job_title")):
        lines.append(f"TITLE:{_esc(_printed(card.get('job_title')))}")
    type_map = {"mobile": "CELL", "fax": "FAX", "phone": "WORK,VOICE", "whatsapp": "CELL", "unknown": "VOICE"}
    for p in card.get("phones") or []:
        num = p.get("e164") or p.get("original")
        if num:
            lines.append(f"TEL;TYPE={type_map.get(p.get('type') or 'unknown', 'VOICE')}:{_esc(num)}")
    for e in card.get("emails") or []:
        if _v(e):
            lines.append(f"EMAIL;TYPE=INTERNET:{_esc(_v(e))}")
    for key in ("website", "linkedin"):
        if _v(card.get(key)):
            lines.append(f"URL:{_esc(_v(card.get(key)))}")
    for s in card.get("social_profiles") or []:
        if _v(s):
            lines.append(f"X-SOCIALPROFILE:{_esc(_v(s))}")
    addr = card.get("address")
    if addr:
        street = addr.get("street") or ""
        lines.append(
            "ADR;TYPE=WORK:;"
            + ";".join(_esc(x or "") for x in (addr.get("building"), street, addr.get("city"), addr.get("region"), addr.get("postal_code"), addr.get("country")))
        )
        # Label: a person's correction wins (built from the corrected parts), then the normalized text,
        # then the raw OCR text. The raw OCR text itself always stays in the JSON record.
        label = addr.get("normalized_text") or addr.get("original_text") or ""
        if addr.get("review_status") == "corrected":
            parts = [addr.get("building"), street, " ".join(x for x in (addr.get("postal_code"), addr.get("city")) if x), addr.get("region"), addr.get("country")]
            label = ", ".join(x for x in parts if x) or label
        lines.append(f"LABEL;TYPE=WORK:{_esc(label)}")
    notes = []
    for key, label in (("qualifications", "Qualifications"), ("certifications", "Certifications"), ("memberships", "Memberships")):
        vals = [_v(x) for x in card.get(key) or [] if _v(x)]
        if vals:
            notes.append(f"{label}: " + "; ".join(vals))
    if _printed(card.get("specialty")):
        notes.append(f"Specialty: {_printed(card.get('specialty'))}")
    if _v(card.get("professional_description")):
        notes.append(_v(card.get("professional_description")))
    if _printed(card.get("industry")):
        notes.append(f"Industry: {_printed(card.get('industry'))}")
    if notes:
        lines.append(f"NOTE:{_esc(' | '.join(notes))}")
    lines.append("END:VCARD")
    return "\r\n".join(_fold(l) for l in lines) + "\r\n"


def _csv_safe(value: str) -> str:
    # CSV/Excel formula injection: a scanned card could contain "=HYPERLINK(...)"
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


BUSINESS_CSV_COLUMNS = [
    "id", "full_name", "first_name", "last_name", "arabic_name", "job_title", "company", "department", "industry",
    "specialty", "professional_description", "phones", "mobile", "telephone", "fax", "emails", "website", "linkedin", "address", "street", "city",
    "postal_code", "country", "qualifications", "languages", "review_status", "updated_at",
]


def _phones_of(d: dict[str, Any], *types: str) -> str:
    return " | ".join(str(p.get("e164") or p.get("original")) for p in d.get("phones") or [] if p.get("type") in types)
def business_row(doc: dict[str, Any]) -> dict[str, str]:
    d = doc.get("data") or {}
    addr = d.get("address") or {}
    return {
        "id": str(doc.get("id", "")),
        "full_name": _v(d.get("full_name")),
        "first_name": _v(d.get("first_name")),
        "last_name": _v(d.get("last_name")),
        "arabic_name": _v(d.get("arabic_name")),
        "job_title": _printed(d.get("job_title")),
        "company": _v(d.get("company")),
        "department": _v(d.get("department")),
        "industry": _printed(d.get("industry")),
        "specialty": _v(d.get("specialty")),
        "professional_description": _v(d.get("professional_description")),
        "mobile": _phones_of(d, "mobile", "whatsapp"),
        "telephone": _phones_of(d, "phone", "unknown"),
        "fax": _phones_of(d, "fax"),
        "street": addr.get("street") or "",
        "qualifications": "; ".join(_v(q) for q in d.get("qualifications") or [] if _v(q)),
        "phones": " | ".join(f"{p.get('type')}:{p.get('e164') or p.get('original')}" for p in d.get("phones") or []),
        "emails": " | ".join(_v(e) for e in d.get("emails") or []),
        "website": _v(d.get("website")),
        "linkedin": _v(d.get("linkedin")),
        "address": (addr.get("original_text") or "").replace("\n", ", "),
        "city": addr.get("city") or "",
        "postal_code": addr.get("postal_code") or "",
        "country": addr.get("country") or "",
        "languages": ",".join(d.get("languages") or []),
        "review_status": str(doc.get("review_status", "")),
        "updated_at": str(doc.get("updated_at", "")),
    }


def to_csv(rows: Iterable[dict[str, str]], columns: list[str]) -> str:
    buf = io.StringIO()
    buf.write("﻿")  # UTF-8 BOM so spreadsheet apps show Arabic correctly
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _csv_safe(v) for k, v in r.items()})
    return buf.getvalue()


def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
