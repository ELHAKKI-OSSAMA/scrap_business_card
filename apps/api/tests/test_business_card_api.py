"""Business-card-only API behaviour (replayed OCR lines, no model inference)."""

from __future__ import annotations

from test_documents import BC, _processed_card

# lines re-typed from the user-described medical card (synthetic, not the user's photo)
MEDICAL = [
    ((0.20, 0.05, 0.80, 0.11), "CABINET D’HÉPATO-GASTROENTÉROLOGIE", 0.97),
    ((0.25, 0.14, 0.75, 0.20), "عيادة أمراض الكبد والجهاز الهضمي", 0.93),
    ((0.25, 0.33, 0.75, 0.41), "Dr ELALAMI IDRISSI Rachid", 0.98),
    ((0.10, 0.45, 0.90, 0.50), "Spécialiste des maladies du foie et de l’appareil digestif", 0.95),
    ((0.35, 0.68, 0.65, 0.73), "16, Av. Hassan II", 0.96),
    ((0.35, 0.78, 0.65, 0.84), "Tél : 05.35.51.11.67", 0.97),
]


def test_medical_card_fields_review_and_exports(client, alice, replay_provider):
    replay_provider.script = MEDICAL
    doc = _processed_card(client, alice, replay_provider)
    d = doc["data"]
    assert d["full_name"]["value"] == "ELALAMI IDRISSI Rachid" and d["full_name"]["original_value"].startswith("Dr")
    assert d["specialty"]["normalized_value"] == "hepato-gastroenterology"
    assert d["professional_description"]["value"].startswith("Spécialiste")
    assert d["job_title"]["value"] == "Médecin" and d["job_title"]["review_status"] == "needs_review"
    assert d["phones"][0]["original"] == "05.35.51.11.67" and d["phones"][0]["e164"] is None
    assert "job_title" in d["review_fields"]

    # computed lists are read-only
    for path in ("review_fields", "qr_checks"):
        r = client.patch(f"{BC}/{doc['id']}/fields", json={"changes": [{"path": path, "value": []}]}, headers=alice["headers"])
        assert r.status_code == 422 and r.json()["error"]["code"] == "read_only_field"

    # vCard never exports the inferred title; confirming it makes it exportable
    vcf = client.get(f"{BC}/{doc['id']}/export?format=vcf", headers=alice["headers"]).text
    assert "TITLE:" not in vcf and "FN:ELALAMI IDRISSI Rachid" in vcf and "05.35.51.11.67" in vcf
    r = client.patch(f"{BC}/{doc['id']}/fields", json={"changes": [{"path": "job_title", "op": "verify"}]}, headers=alice["headers"])
    assert r.status_code == 200
    assert "job_title" not in r.json()["data"]["review_fields"], "review list refreshed after verification"
    vcf = client.get(f"{BC}/{doc['id']}/export?format=vcf", headers=alice["headers"]).text
    assert "TITLE:Médecin" in vcf

    csv = client.get(f"{BC}/{doc['id']}/export?format=csv", headers=alice["headers"]).text
    assert csv.startswith("﻿") and "Spécialiste des maladies du foie" in csv


def test_phone_country_from_printed_address(client, alice, replay_provider):
    replay_provider.script = [
        ((0.1, 0.05, 0.6, 0.12), "Karim BENNANI", 0.98),
        ((0.1, 0.20, 0.6, 0.26), "Tél : 05 22 48 17 30", 0.97),
        ((0.1, 0.60, 0.6, 0.66), "25, Rue Ibn Battouta", 0.96),
        ((0.1, 0.68, 0.6, 0.74), "20250 Casablanca - Maroc", 0.96),
    ]
    d = _processed_card(client, alice, replay_provider)["data"]
    p = d["phones"][0]
    assert p["e164"] == "+212522481730" and p["region_inferred_from"] == "card_address" and p["review_status"] == "needs_review"
