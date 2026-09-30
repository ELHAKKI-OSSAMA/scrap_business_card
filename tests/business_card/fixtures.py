"""SYNTHETIC business-card fixtures (computer-rendered; all people, companies, numbers are fictitious
except the layout/text of the user-described medical card, which is re-typed from the user's
description — NOT the user's photograph).

Each case returns images per side and the ground truth that was actually rendered. Nothing here
is fed to the extractor except the pixels.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "datasets" / "synthetic"))
from generate import Canvas, degrade  # noqa: E402

import random  # noqa: E402

SYNTHETIC = {"source": "synthetic", "note": "computer-rendered test fixture, not a real card"}


@dataclass
class Case:
    key: str
    description: str
    images: dict[str, Image.Image]
    truth: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


def _card(w=1050, h=600) -> Canvas:
    return Canvas(w, h, bg=(252, 251, 248))


def _qr(img: Image.Image, payload: str, x: int, y: int, size: int) -> None:
    # cv2.QRCodeEncoder (4.10) emits invalid symbols above version ~7, so fixtures use zxing-cpp
    # (test-data dependency only; the product decodes with cv2.QRCodeDetector).
    import zxingcpp

    code = np.array(zxingcpp.create_barcode(payload, zxingcpp.BarcodeFormat.QRCode).to_image(scale=4, add_quiet_zones=False))
    q = Image.fromarray(code).convert("RGB").resize((size, size), Image.NEAREST)
    # quiet zone
    pad = Image.new("RGB", (size + 24, size + 24), (255, 255, 255))
    pad.paste(q, (12, 12))
    img.paste(pad, (x, y))


def _logo(img: Image.Image, x: int, y: int, r: int = 55, color=(214, 90, 40)) -> None:
    d = ImageDraw.Draw(img)
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=color)
    d.rectangle([x + r * 0.55, y + r * 0.55, x + r * 1.45, y + r * 1.45], fill=(255, 255, 255))


# ------------------------------------------------------------------ cards

def english() -> Case:
    c = _card()
    c.text(70, 70, "James Carter", 54, "latin_bold", lang="en")
    c.text(70, 145, "Project Manager", 34, lang="en")
    c.text(70, 195, "Northwind Consulting Ltd", 34, lang="en")
    c.text(70, 330, "Tel: +44 20 7946 0958", 30, lang="en")
    c.text(70, 380, "james.carter@northwind-consulting.co.uk", 30, lang="en")
    c.text(70, 430, "www.northwind-consulting.co.uk", 30, lang="en")
    c.text(70, 490, "10 King Street, London, United Kingdom", 28, lang="en")
    return Case("A_english", "English, landscape", {"front": c.img}, {
        "full_name": "James Carter", "job_title": "Project Manager", "company": "Northwind Consulting Ltd",
        "phones_e164": ["+442079460958"], "emails": ["james.carter@northwind-consulting.co.uk"],
        "website": "northwind-consulting.co.uk", "languages": {"en"}}, {"phone", "email", "website", "address", "landscape"})


def french() -> Case:
    c = _card()
    c.text(70, 60, "Hélène DUPONT", 54, "latin_bold", lang="fr")
    c.text(70, 135, "Directrice Générale", 34, lang="fr")
    c.text(70, 185, "Atlas Structures SARL", 34, lang="fr")
    c.text(70, 300, "Tél : +212 5 22 48 17 30", 30, lang="fr")
    c.text(70, 350, "Mob : +212 6 61 23 45 67", 30, lang="fr")
    c.text(70, 400, "h.dupont@atlas-structures.ma", 30, lang="fr")
    c.text(70, 450, "www.atlas-structures.ma", 30, lang="fr")
    c.text(620, 400, "25, Rue Ibn Battouta", 28, lang="fr")
    c.text(620, 445, "20250 Casablanca - Maroc", 28, lang="fr")
    return Case("B_french", "French, accents, typed phones, address", {"front": c.img}, {
        "full_name": "Hélène DUPONT", "job_title": "Directrice Générale", "company": "Atlas Structures SARL",
        "phones_e164": ["+212522481730", "+212661234567"], "phone_types": {"+212522481730": "phone", "+212661234567": "mobile"},
        "emails": ["h.dupont@atlas-structures.ma"], "website": "atlas-structures.ma",
        "postal_code": "20250", "city": "Casablanca", "languages": {"fr"}}, {"phone", "email", "website", "address", "landscape"})


def arabic() -> Case:
    c = _card()
    c.text(980, 60, "كريم بناني", 56, align="right", lang="ar")
    c.text(980, 145, "مدير المبيعات", 36, align="right", lang="ar")
    c.text(980, 205, "شركة أطلس للهياكل", 36, align="right", lang="ar")
    c.text(980, 330, "الهاتف: 0522481730", 32, align="right", lang="ar")
    c.text(980, 400, "25 شارع ابن بطوطة، الدار البيضاء", 30, align="right", lang="ar")
    c.text(70, 470, "karim@atlas-structures.ma", 30, lang="en")
    return Case("C_arabic", "Arabic RTL with Latin email", {"front": c.img}, {
        "arabic_name": "كريم بناني", "job_title": "مدير المبيعات", "company": "شركة أطلس للهياكل",
        "emails": ["karim@atlas-structures.ma"], "phone_digits": ["0522481730"], "languages": {"ar"}}, {"phone", "email", "address", "landscape"})


def medical_ar_fr() -> Case:
    """Re-typed from the user's description of a real medical card (text only, own layout)."""
    c = _card()
    c.text(525, 40, "CABINET D’HÉPATO-GASTROENTÉROLOGIE", 34, "latin_bold", align="center", lang="fr")
    c.text(525, 95, "عيادة أمراض الكبد والجهاز الهضمي", 34, align="center", lang="ar")
    c.text(525, 210, "Dr ELALAMI IDRISSI Rachid", 46, "latin_bold", align="center", lang="fr")
    c.text(525, 280, "Spécialiste des maladies du foie et de l’appareil digestif", 26, align="center", lang="fr")
    c.text(525, 420, "16, Av. Hassan II", 28, align="center", lang="fr")
    c.text(525, 480, "Tél : 05.35.51.11.67", 30, align="center", lang="fr")
    return Case("D_medical_ar_fr", "Arabic + French medical card (user-described text, synthetic render)", {"front": c.img}, {
        "full_name_contains": "ELALAMI IDRISSI Rachid", "company_contains": "GASTRO", "specialty_contains": "gastro",
        "phone_digits": ["0535511167"], "street_contains": "Hassan II", "arabic_line": "عيادة أمراض الكبد والجهاز الهضمي",
        "languages": {"ar", "fr"}}, {"phone", "address", "landscape", "medical"})


def arabic_english() -> Case:
    c = _card()
    c.text(70, 60, "Omar Haddad", 50, "latin_bold", lang="en")
    c.text(980, 60, "عمر حداد", 50, align="right", lang="ar")
    c.text(70, 135, "Software Engineer", 32, lang="en")
    c.text(980, 135, "مهندس برمجيات", 32, align="right", lang="ar")
    c.text(70, 200, "Haddad Technologies Inc", 32, lang="en")
    c.text(70, 330, "Mobile: +971 50 123 4567", 30, lang="en")
    c.text(70, 380, "omar@haddad-tech.ae", 30, lang="en")
    c.text(70, 430, "linkedin.com/in/omarhaddad", 30, lang="en")
    return Case("E_arabic_english", "Arabic + English, LinkedIn", {"front": c.img}, {
        "full_name": "Omar Haddad", "arabic_name": "عمر حداد", "job_title": "Software Engineer",
        "phones_e164": ["+971501234567"], "phone_types": {"+971501234567": "mobile"},
        "emails": ["omar@haddad-tech.ae"], "linkedin_contains": "linkedin.com/in/omarhaddad", "languages": {"ar", "en"}}, {"phone", "email", "website", "landscape"})


def french_english() -> Case:
    c = _card()
    c.text(70, 60, "Sophie MARTIN", 52, "latin_bold", lang="fr")
    c.text(70, 135, "Consultante Senior | Senior Consultant", 30, lang="fr")
    c.text(70, 190, "Cabinet Martin & Associés", 32, lang="fr")
    c.text(70, 320, "Tél. +33 1 42 68 53 00", 30, lang="fr")
    c.text(70, 370, "s.martin@martin-associes.fr", 30, lang="fr")
    c.text(70, 420, "www.martin-associes.fr", 30, lang="fr")
    c.text(70, 480, "8 rue de la Paix, 75002 Paris, France", 28, lang="fr")
    return Case("F_french_english", "French + English bilingual title", {"front": c.img}, {
        "full_name": "Sophie MARTIN", "company": "Cabinet Martin & Associés", "phones_e164": ["+33142685300"],
        "emails": ["s.martin@martin-associes.fr"], "website": "martin-associes.fr", "postal_code": "75002", "city": "Paris",
        "languages": {"fr", "en"}}, {"phone", "email", "website", "address", "landscape"})


def trilingual() -> Case:
    c = _card()
    c.text(70, 50, "Salma EL IDRISSI", 48, "latin_bold", lang="fr")
    c.text(980, 50, "سلمى الإدريسي", 48, align="right", lang="ar")
    c.text(70, 120, "Ingénieur Civil / Civil Engineer", 30, lang="fr")
    c.text(980, 170, "مهندسة مدنية", 30, align="right", lang="ar")
    c.text(70, 175, "Atlas Structures SARL", 30, lang="fr")
    c.text(70, 320, "Tél : +212 5 37 70 12 34", 28, lang="fr")
    c.text(70, 365, "Mobile: +212 6 70 11 22 33", 28, lang="en")
    c.text(70, 410, "salma.idrissi@atlas-structures.ma", 28, lang="en")
    c.text(70, 460, "12 Avenue Mohammed V, 10000 Rabat, Maroc", 26, lang="fr")
    return Case("G_trilingual", "Arabic + French + English", {"front": c.img}, {
        "full_name": "Salma EL IDRISSI", "arabic_name": "سلمى الإدريسي", "company": "Atlas Structures SARL",
        "phones_e164": ["+212537701234", "+212670112233"], "emails": ["salma.idrissi@atlas-structures.ma"],
        "postal_code": "10000", "city": "Rabat", "languages": {"ar", "fr", "en"}}, {"phone", "email", "address", "landscape"})


def with_qr() -> Case:
    c = _card()
    c.text(70, 70, "Karim BENNANI", 52, "latin_bold", lang="fr")
    c.text(70, 145, "Responsable Commercial", 32, lang="fr")
    c.text(70, 200, "Groupe Medina Distribution", 32, lang="fr")
    c.text(70, 340, "Tél : +212 5 22 96 11 68", 30, lang="fr")
    c.text(70, 390, "k.bennani@medina-distribution.com", 30, lang="fr")
    vcard = ("BEGIN:VCARD\nVERSION:3.0\nFN:Karim Bennani\nORG:Groupe Medina Distribution\n"
             "TEL;TYPE=CELL:+212661000111\nEMAIL:k.bennani@medina-distribution.com\nEND:VCARD")
    _qr(c.img, vcard, 760, 300, 230)
    return Case("K_qr_vcard", "QR vCard whose phone differs from the printed phone (conflict)", {"front": c.img}, {
        "full_name": "Karim BENNANI", "phones_e164": ["+212522961168"], "emails": ["k.bennani@medina-distribution.com"],
        "qr_kind": "vcard", "qr_tel": "+212661000111", "languages": {"fr"}}, {"qr", "phone", "email", "landscape"})


def with_logo() -> Case:
    c = _card()
    _logo(c.img, 820, 60)
    c.text(70, 70, "Laura Bennett", 52, "latin_bold", lang="en")
    c.text(70, 145, "Chief Executive Officer", 32, lang="en")
    c.text(70, 200, "Bennett Holding", 32, lang="en")
    c.text(70, 350, "laura@bennett-holding.com", 30, lang="en")
    c.text(70, 400, "+1 415 555 0142", 30, lang="en")
    return Case("M_logo", "Logo graphic next to text", {"front": c.img}, {
        "full_name": "Laura Bennett", "company": "Bennett Holding", "emails": ["laura@bennett-holding.com"],
        "phones_e164": ["+14155550142"], "logo": True, "languages": {"en"}}, {"logo", "email", "phone", "landscape"})


def portrait() -> Case:
    c = Canvas(600, 1050, bg=(252, 251, 248))
    c.text(300, 120, "Youssef EL AMRANI", 44, "latin_bold", align="center", lang="fr")
    c.text(300, 190, "Avocat", 34, align="center", lang="fr")
    c.text(300, 250, "Cabinet Alaoui & Associés", 30, align="center", lang="fr")
    c.text(300, 600, "Tél : +212 5 37 20 30 40", 28, align="center", lang="fr")
    c.text(300, 650, "y.elamrani@alaoui-avocats.ma", 26, align="center", lang="fr")
    c.text(300, 700, "www.alaoui-avocats.ma", 26, align="center", lang="fr")
    return Case("N_portrait", "Portrait orientation, centred layout", {"front": c.img}, {
        "full_name": "Youssef EL AMRANI", "job_title": "Avocat", "company": "Cabinet Alaoui & Associés",
        "phones_e164": ["+212537203040"], "emails": ["y.elamrani@alaoui-avocats.ma"], "website": "alaoui-avocats.ma",
        "languages": {"fr"}}, {"portrait", "phone", "email", "website"})


def front_back() -> Case:
    f = french()
    b = _card()
    b.text(980, 80, "هيلين دوبون", 52, align="right", lang="ar")
    b.text(980, 160, "المديرة العامة", 34, align="right", lang="ar")
    b.text(980, 230, "شركة أطلس للهياكل", 34, align="right", lang="ar")
    truth = dict(f.truth, arabic_name="هيلين دوبون", languages={"fr", "ar"})
    return Case("P_front_back", "French front, Arabic back", {"front": f.images["front"], "back": b.img}, truth, {"front_back", "phone", "email"})


def low_quality() -> Case:
    f = french()
    rng = random.Random(7)
    img = degrade(degrade(f.images["front"], "low_res", rng), "noisy", rng)
    return Case("Q_low_quality", "French card at 1/3 resolution with noise", {"front": img}, f.truth, {"low_quality"})


def rotated() -> Case:
    f = french()
    return Case("R_rotated", "French card rotated 7°", {"front": f.images["front"].rotate(7, expand=True, fillcolor=(200, 200, 200))}, f.truth, {"rotated"})


def rotated90() -> Case:
    f = english()
    return Case("R_rotated90", "English card rotated 90° (photo taken sideways)", {"front": f.images["front"].rotate(90, expand=True)}, f.truth, {"rotated"})


def partially_unreadable() -> Case:
    f = french()
    img = f.images["front"].copy()
    d = ImageDraw.Draw(img)
    d.rectangle([60, 345, 330, 390], fill=(30, 30, 30))  # hides the start of the mobile number
    d.rectangle([60, 395, 260, 440], fill=(30, 30, 30))  # hides the start of the e-mail
    truth = {"full_name": "Hélène DUPONT", "phones_e164": ["+212522481730"], "hidden_phone": "+212661234567", "hidden_email": "h.dupont@atlas-structures.ma"}
    return Case("S_partially_unreadable", "Parts of the mobile number and e-mail covered", {"front": img}, truth, {"partial"})


ALL = [english, french, arabic, medical_ar_fr, arabic_english, french_english, trilingual, with_qr, with_logo, portrait, front_back, low_quality, rotated, rotated90, partially_unreadable]


def build_all() -> list[Case]:
    return [f() for f in ALL]


def to_rgb(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB"))
