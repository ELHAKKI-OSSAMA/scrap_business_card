"""Business Card test suite — real PaddleOCR on SYNTHETIC fixtures (see fixtures.py).

Covers OCR, extraction, validation, confidence, review flags and exports per case. Save /
retrieval / API export are exercised against a running stack by api_suite.py.
"""

from __future__ import annotations

import csv
import io
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from extraction import extract_business_card  # noqa: E402
from extraction.export import BUSINESS_CSV_COLUMNS, business_row, to_csv, to_vcard  # noqa: E402
from shared_types import OcrPage, Side  # noqa: E402

pytestmark = pytest.mark.skipif(importlib.util.find_spec("paddleocr") is None, reason="PaddleOCR not installed")

import fixtures as F  # noqa: E402

_RESULTS: dict[str, tuple] = {}


def run(case_fn):
    from harness import run_case

    key = case_fn.__name__
    if key not in _RESULTS:
        case = case_fn()
        pages, ex, regions, timings = run_case(case)
        _RESULTS[key] = (case, pages, ex.model_dump(mode="json"), regions)
    return _RESULTS[key]


def v(d, k):
    return (d.get(k) or {}).get("value")


def ocr_text(pages) -> str:
    return "\n".join(l.text for p in pages for l in p.lines)


def check_common(case, pages, d):
    t = case.truth
    # OCR produced lines, every line has a box and a confidence
    lines = [l for p in pages for l in p.lines]
    assert lines, "no OCR text"
    assert all(l.bbox.w > 0 and l.confidence is not None for l in lines)
    if "full_name" in t:
        assert v(d, "full_name") == t["full_name"]
    if "arabic_name" in t:
        assert v(d, "arabic_name") == t["arabic_name"]
    if "job_title" in t:
        assert v(d, "job_title") == t["job_title"]
    if "company" in t:
        assert v(d, "company") == t["company"]
    if "phones_e164" in t:
        assert {p["e164"] for p in d["phones"]} >= set(t["phones_e164"])
    for e164, kind in (t.get("phone_types") or {}).items():
        assert next(p for p in d["phones"] if p["e164"] == e164)["type"] == kind
    if "emails" in t:
        assert [e["value"] for e in d["emails"]] == t["emails"]
        assert all(e["confidence"] is not None and e["source_region_ids"] for e in d["emails"])
    if "website" in t:
        assert v(d, "website").endswith(t["website"])
    if "postal_code" in t:
        assert d["address"]["postal_code"] == t["postal_code"]
    if "city" in t:
        assert d["address"]["city"] == t["city"]
    if "languages" in t:
        assert set(t["languages"]) <= set(d["languages"])
    # every extracted scalar keeps its evidence
    for k in ("full_name", "company", "job_title", "website"):
        f = d.get(k) or {}
        if f.get("value") is not None and not str(f.get("notes") or "").startswith("inferred"):
            assert f["original_value"], k
            assert f["source_region_ids"], k
            assert f["extraction_method"] in ("rule", "layout", "ocr", "qr")
            assert f["review_status"] in ("unreviewed", "needs_review")


# ---------------------------------------------------------------- per-case (A–S)

@pytest.mark.parametrize("case_fn", [F.english, F.french, F.arabic, F.arabic_english, F.french_english, F.trilingual, F.with_logo, F.portrait, F.front_back, F.low_quality, F.rotated, F.rotated90], ids=lambda f: f.__name__)
def test_case_fields(case_fn):
    case, pages, d, _ = run(case_fn)
    check_common(case, pages, d)


def test_A_english_title_and_url_preserved():
    case, pages, d, _ = run(F.english)
    assert "james.carter@northwind-consulting.co.uk" in ocr_text(pages)
    assert v(d, "job_title") == "Project Manager"


def test_B_french_accents_and_phone_labels():
    case, pages, d, _ = run(F.french)
    assert "Hélène DUPONT" in ocr_text(pages) and "Générale" in ocr_text(pages)
    assert d["phones"][0]["type_evidence"] and d["phones"][1]["type"] == "mobile"
    assert all(p["region_inferred_from"] == "explicit_prefix" for p in d["phones"])


def test_C_arabic_preserved_rtl_and_phone_not_guessed():
    case, pages, d, _ = run(F.arabic)
    arabic_lines = [l for p in pages for l in p.lines if l.script.value == "Arab"]
    assert arabic_lines and all(l.direction.value == "rtl" for l in arabic_lines)
    assert v(d, "arabic_name") == "كريم بناني"
    assert v(d, "job_title") == "مدير المبيعات"
    # no country printed on the card and no default configured -> never normalised
    p = d["phones"][0]
    assert p["original"].replace(" ", "") == "0522481730" and p["e164"] is None and p["review_status"] == "needs_review"


def test_D_medical_card_user_described_text():
    case, pages, d, _ = run(F.medical_ar_fr)
    text = ocr_text(pages)
    assert case.truth["arabic_line"] in text, "Arabic clinic line must be read verbatim"
    assert "ELALAMI IDRISSI Rachid" in v(d, "full_name")
    assert d["full_name"]["original_value"].startswith("Dr"), "honorific kept in the original value"
    assert "GASTRO" in v(d, "company").upper()
    assert d["specialty"]["normalized_value"] == "hepato-gastroenterology"
    assert d["specialty"]["notes"] == "explicit specialty term printed on the card"
    assert v(d, "professional_description").startswith("Spécialiste des maladies du foie")
    # job title is not printed: inferred and flagged, never presented as read
    assert v(d, "job_title") == "Médecin" and d["job_title"]["review_status"] == "needs_review" and d["job_title"]["original_value"] is None
    ph = d["phones"][0]
    assert ph["original"] == "05.35.51.11.67" and ph["e164"] is None, "no country on the card -> not normalised"
    assert "Hassan II" in d["address"]["street"]
    assert "job_title" in d["review_fields"] and "phones.0" in d["review_fields"]


def test_E_linkedin_detected():
    case, pages, d, _ = run(F.arabic_english)
    assert "linkedin.com/in/omarhaddad" in v(d, "linkedin")


def test_K_qr_decoded_and_conflict_surfaced_not_resolved():
    case, pages, d, regions = run(F.with_qr)
    assert d["qr_codes"] and d["qr_codes"][0]["kind"] == "vcard"
    assert d["qr_codes"][0]["imported"] is False
    assert d["qr_codes"][0]["parsed"]["tel"] == ["+212661000111"]
    checks = {(c["field"], c["status"]) for c in d["qr_checks"]}
    assert ("full_name", "match") in checks and ("emails", "match") in checks
    assert ("phones", "qr_only") in checks
    assert "+212661000111" not in [p["e164"] for p in d["phones"]], "QR value must not be imported automatically"
    assert any(r.label == "qr" for r in regions)


def test_M_logo_candidate_detected():
    case, pages, d, regions = run(F.with_logo)
    assert d["logo"] is not None and d["logo"]["label"] == "logo"
    assert v(d, "job_title") == "Chief Executive Officer"


def test_N_portrait_layout():
    case, pages, d, _ = run(F.portrait)
    assert pages[0].height > pages[0].width
    check_common(case, pages, d)


def test_P_front_back_merged():
    case, pages, d, _ = run(F.front_back)
    assert {p.side.value for p in pages} == {"front", "back"}
    ids = d["arabic_name"]["source_region_ids"]
    assert ids and ids[0].startswith("b-"), "Arabic name read from the back side"


def test_Q_low_quality_warns():
    case, pages, d, _ = run(F.low_quality)
    assert any("low_resolution" in w for w in d["warnings"])


def test_S_partial_card_does_not_invent():
    case, pages, d, _ = run(F.partially_unreadable)
    assert case.truth["hidden_phone"] not in [p["e164"] for p in d["phones"]]
    assert case.truth["hidden_email"] not in [e["value"] for e in d["emails"]]
    assert v(d, "website") == "https://www.atlas-structures.ma", "fragment must not replace the explicit URL"
    assert any(str(s.get("notes", "")).startswith("possible_fragment_of") for s in d["social_profiles"])
    assert any(w.startswith("possible_partial_text") for w in d["warnings"])


# ---------------------------------------------------------------- exports

def test_exports_medical_card_arabic_and_no_inferred_title():
    case, pages, d, _ = run(F.medical_ar_fr)
    vcf = to_vcard(d)
    assert vcf.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n") and vcf.rstrip().endswith("END:VCARD")
    assert "FN:ELALAMI IDRISSI Rachid" in vcf
    assert "TEL;TYPE=WORK,VOICE:05.35.51.11.67" in vcf
    assert "TITLE:" not in vcf, "inferred job title must not be exported as read"
    assert "Specialty: HÉPATO-GASTROENTÉROLOGIE" in vcf.replace("\r\n ", "")
    assert "EMAIL" not in vcf and "URL" not in vcf, "nothing that was not extracted"
    out = to_csv([business_row({"id": "x", "data": d})], BUSINESS_CSV_COLUMNS)
    row = next(csv.DictReader(io.StringIO(out.lstrip("﻿"))))
    assert row["job_title"] == "" and row["telephone"] == "05.35.51.11.67"
    assert row["professional_description"].startswith("Spécialiste")


def test_exports_arabic_unicode_preserved():
    case, pages, d, _ = run(F.arabic)
    vcf = to_vcard(d)
    assert "كريم بناني" in vcf.replace("\r\n ", "")
    out = to_csv([business_row({"id": "x", "data": d})], BUSINESS_CSV_COLUMNS)
    assert "كريم بناني" in out and out.startswith("﻿")


def test_csv_typed_phone_columns():
    case, pages, d, _ = run(F.french)
    row = next(csv.DictReader(io.StringIO(to_csv([business_row({"id": "x", "data": d})], BUSINESS_CSV_COLUMNS).lstrip("﻿"))))
    # leading "'" is the CSV formula-injection guard for values starting with "+"
    assert row["telephone"] == "'+212522481730" and row["mobile"] == "'+212661234567" and row["fax"] == ""


# ---------------------------------------------------------------- deterministic (no OCR)

def _page(rows: list[str]) -> OcrPage:
    sys.path.insert(0, str(HERE.parent / "core"))
    from conftest import make_page

    return make_page(Side.front, [(t, (50, 40 + i * 60, 600, 40)) for i, t in enumerate(rows)], height=700)


def test_phone_normalised_only_with_country_printed_on_card():
    ex, _ = extract_business_card([_page(["Karim BENNANI", "Tél : 05 22 48 17 30", "25, Rue Ibn Battouta", "20250 Casablanca - Maroc"])])
    p = ex.phones[0]
    assert p.e164 == "+212522481730" and p.region_inferred_from == "card_address" and p.review_status.value == "needs_review"
    ex2, _ = extract_business_card([_page(["Karim BENNANI", "Tél : 05 22 48 17 30", "25, Rue Ibn Battouta", "Casablanca"])])
    assert ex2.phones[0].e164 is None, "city alone is not a reliable country"


def test_arabic_language_alone_never_sets_country():
    ex, _ = extract_business_card([_page(["كريم بناني", "الهاتف 0522481730"])])
    assert ex.phones[0].e164 is None


def test_invalid_email_kept_but_flagged():
    ex, _ = extract_business_card([_page(["Karim BENNANI", "karim@@atlas..ma", "karim@atlas.ma"])])
    assert [e.value for e in ex.emails] == ["karim@atlas.ma"]


def test_first_line_is_not_assumed_to_be_the_name():
    ex, _ = extract_business_card([_page(["Atlas Structures SARL", "Hélène DUPONT", "Directrice Générale"])])
    assert ex.full_name.value == "Hélène DUPONT" and ex.company.value == "Atlas Structures SARL"


def test_no_specialty_invented_without_explicit_term():
    ex, _ = extract_business_card([_page(["Dr Karim BENNANI", "Spécialiste des maladies du foie et de l'appareil digestif"])])
    assert ex.specialty.value is None, "a description is not mapped to a specialty the card does not print"
    assert ex.job_title.value is None
    assert ex.professional_description.value.startswith("Spécialiste")


def test_qr_payload_never_executed_classification():
    from ocr_core.qr import classify_qr

    assert classify_qr("javascript:alert(1)")[0] == "text"
    assert classify_qr("BEGIN:VCARD\nFN:A\nEND:VCARD")[0] == "vcard"


def test_vcard_label_follows_corrected_address_not_raw_ocr():
    auto = {"original_text": "16, Av. Hassan ll", "normalized_text": "16, Av. Hassan II", "street": "16, Av. Hassan II"}
    assert "LABEL;TYPE=WORK:16\, Av. Hassan II" in to_vcard({"full_name": {"value": "X"}, "address": auto})
    human = {"original_text": "16, Av. Hassan ll", "street": "16, Av. Hassan II", "city": "Fès", "review_status": "corrected"}
    vcf = to_vcard({"full_name": {"value": "X"}, "address": human})
    assert "LABEL;TYPE=WORK:16\, Av. Hassan II\, Fès" in vcf and "Hassan ll" not in vcf
