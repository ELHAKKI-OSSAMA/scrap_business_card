"""Vision-LLM (Ollama) answer parsing, grounding and key failover — no network."""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import ValidationError

from extraction import extract_business_card, merge_vision, parse_card_json, vision_enrich
from extraction.vision_llm import OllamaVisionClient
from shared_types import ExtractionMethod, ReviewStatus, Side

ROWS = [
    ("OMNISHORE", (50, 20, 400, 50)),
    ("MEDTECH GROUP", (200, 75, 180, 20)),
    ("Mahmoud ATIF", (50, 150, 220, 30)),
    ("Directeur de Projet Senior", (50, 190, 240, 20)),
    ("& Delivery Manager", (50, 215, 180, 20)),
    ("Mob:+212 666 61 90 87", (50, 300, 220, 20)),
    ("Matif@omnidata.ma", (50, 325, 180, 20)),
    ("Technopark Casablanca", (450, 150, 230, 20)),
    ("Rte de Nouaceur - N° 502", (450, 175, 230, 20)),
    ("5º étg.- 16 428 Casablanca", (450, 200, 230, 20)),
    ("Tél.:+212 522 52 38 40", (450, 280, 230, 20)),
    ("+212 522 52 11 38", (500, 305, 180, 20)),
    ("Fax :+212 522 98 75 05", (450, 330, 230, 20)),
]

ANSWER = {
    "full_name": "Mahmoud ATIF", "first_name": "Mahmoud", "last_name": "ATIF",
    "job_title": "Directeur de Projet Senior & Delivery Manager", "company": "OMNISHORE MEDTECH GROUP",
    "department": None, "emails": ["Matif@omnidata.ma"], "website": None,
    "phones": [{"type": "mobile", "number": "+212 666 61 90 87"}, {"type": "phone", "number": "+212 522 52 38 40"},
               {"type": "phone", "number": "+212 522 52 11 38"}, {"type": "fax", "number": "+212 522 98 75 05"}],
    "address": {"street": "Rte de Nouaceur - N° 502", "building": "Technopark Casablanca", "postal_code": "16 428",
                "city": "Casablanca", "region": None, "country": None},
}


def _base(page_factory):
    page = page_factory(Side.front, ROWS)
    ex = extract_business_card([page])[0]
    return ex, page.lines


def test_parse_accepts_fenced_json_and_rejects_unknown_keys():
    assert parse_card_json("```json\n" + json.dumps(ANSWER) + "\n```").company == "OMNISHORE MEDTECH GROUP"
    with pytest.raises(ValidationError):
        parse_card_json(json.dumps({**ANSWER, "name": "x"}))
    with pytest.raises(ValueError):
        parse_card_json("Here is the card: {}")


def test_merge_grounded_values_marked_for_review(page_factory):
    ex, lines = _base(page_factory)
    out = merge_vision(ex, parse_card_json(json.dumps(ANSWER)), lines, model="gemma4:31b")
    assert out.company.value == "OMNISHORE MEDTECH GROUP"
    assert out.company.extraction_method == ExtractionMethod.llm and out.company.review_status == ReviewStatus.needs_review
    assert out.job_title.value == "Directeur de Projet Senior & Delivery Manager"
    assert [p.type for p in out.phones] == ["mobile", "phone", "phone", "fax"]
    assert out.address.street == "Rte de Nouaceur - N° 502" and out.address.postal_code == "16 428"
    assert out.address.country is None
    assert "company" in out.review_fields and out.extractor == "rules+vision:gemma4:31b"


def test_merge_rejects_values_not_in_ocr_text(page_factory):
    ex, lines = _base(page_factory)
    bad = {**ANSWER, "company": "Acme Corp", "emails": ["ceo@acme.com"], "phones": [{"type": "mobile", "number": "+212 600 00 00 00"}],
           "address": {"street": None, "building": None, "postal_code": None, "city": "Rabat", "region": None, "country": "Maroc"}}
    out = merge_vision(ex, parse_card_json(json.dumps(bad)), lines, model="m")
    assert out.company.value != "Acme Corp"
    assert all("acme" not in (e.value or "") for e in out.emails)
    assert all(p.e164 != "+212600000000" for p in out.phones)
    assert out.address is None or (out.address.city != "Rabat" and out.address.country is None)
    for w in ("llm_rejected:company:not_in_ocr_text", "llm_rejected:phone:not_in_ocr_text", "llm_rejected:address.country:not_in_ocr_text"):
        assert w in out.warnings


def test_key_failover_and_fallback(page_factory, monkeypatch):
    ex, lines = _base(page_factory)
    used = []

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002
        key = headers["Authorization"].split()[1]
        used.append(key)
        req = httpx.Request("POST", url)
        if key == "k1":
            return httpx.Response(429, request=req)
        return httpx.Response(200, request=req, json={"message": {"content": __import__("json").dumps(ANSWER)}})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = vision_enrich(ex, [b"img"], lines, OllamaVisionClient(model="m", api_keys=["k1", "k2"]))
    assert used == ["k1", "k2"] and out.company.value == "OMNISHORE MEDTECH GROUP"

    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(503, request=httpx.Request("POST", "x")))
    out = vision_enrich(ex, [b"img"], lines, OllamaVisionClient(model="m", api_keys=["k1", "k2"]))
    assert "llm_unavailable_fallback_rules" in out.warnings and out.company.value == ex.company.value


# --- cloud-only engine (OCR_PROVIDER=ollama) ---------------------------------------------------

def _cloud_answer():
    lines = [{"text": t, "box": [50, 30 + 40 * i, 600, 60 + 40 * i]} for i, (t, _) in enumerate(ROWS)]
    return json.dumps({"lines": lines, "card": ANSWER})


class _FakeClient:
    model = "gemma4:31b"

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    def chat(self, prompt, images):
        self.calls += 1
        return self.answers.pop(0)


def test_cloud_engine_builds_page_and_card():
    import numpy as np

    from extraction import OllamaCloudEngine, merge_vision

    eng = OllamaCloudEngine(_FakeClient([_cloud_answer()]))
    page, img = eng.process_page(np.full((400, 700, 3), 255, np.uint8), Side.front)
    assert [l.text for l in page.lines][:3] == ["OMNISHORE", "MEDTECH GROUP", "Mahmoud ATIF"]
    assert all(l.confidence is None and l.bbox.w > 0 for l in page.lines)
    ex = extract_business_card([page])[0]
    ex = merge_vision(ex, eng.cards[Side.front], page.lines, model="gemma4:31b")
    assert ex.company.value == "OMNISHORE MEDTECH GROUP" and len(ex.phones) == 4


def test_cloud_parse_repairs_shape_and_retries():
    import numpy as np

    from extraction import OllamaCloudEngine, parse_cloud_read

    raw = json.dumps({"lines": ["Mahmoud ATIF", {"text": "Matif@omnidata.ma", "box": [1, 2]}, 42],
                      "card": {"full_name": "Mahmoud ATIF", "linkedin": "x", "phones": [{"type": "tel", "number": "+212 666 61 90 87", "label": "Mob"}]}})
    read, notes = parse_cloud_read(raw)
    assert [l.text for l in read.lines] == ["Mahmoud ATIF", "Matif@omnidata.ma"]
    assert read.card.phones[0].type == "unknown"
    assert "cloud_ocr:line_dropped" in notes and "cloud_ocr:box_missing" in notes and any(n.startswith("cloud_ocr:ignored_keys:linkedin") for n in notes)
    fake = _FakeClient(["not json", _cloud_answer()])
    page, _ = OllamaCloudEngine(fake).process_page(np.full((400, 700, 3), 255, np.uint8), Side.front)
    assert fake.calls == 2 and page.lines
    with pytest.raises(ValueError):
        OllamaCloudEngine(_FakeClient(["nope", "still nope"])).process_page(np.full((40, 70, 3), 255, np.uint8), Side.front)
