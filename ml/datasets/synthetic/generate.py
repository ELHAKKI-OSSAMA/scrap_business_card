"""Synthetic business-card generator with ground-truth annotations.

All people, companies, phone numbers and addresses are FICTITIOUS (numbers use valid national
formats but random subscriber digits). Samples are marked ``"source": "synthetic"``; results
on them must never be reported as real-world accuracy.

Arabic is shaped with ``arabic-reshaper`` + ``python-bidi`` when Pillow lacks libraqm, so the
rendered pixels are correct RTL text.

Usage:
    python ml/datasets/synthetic/generate.py --out ml/datasets/synthetic/out --n 6 --seed 7
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

FONT_CANDIDATES = {
    "latin": [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "latin_bold": [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "arabic": [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def _font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    raise SystemExit(f"No font found for {kind}; install fonts-noto-core or run on Windows")


def _is_arabic(s: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in s)


def _shape(s: str) -> tuple[str, dict]:
    if not _is_arabic(s):
        return s, {}
    if features.check("raqm"):
        return s, {"direction": "rtl", "language": "ar"}
    import arabic_reshaper
    from bidi.algorithm import get_display

    return get_display(arabic_reshaper.reshape(s)), {}


@dataclass
class Canvas:
    w: int
    h: int
    bg: tuple[int, int, int] = (250, 250, 247)
    lines: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.img = Image.new("RGB", (self.w, self.h), self.bg)
        self.draw = ImageDraw.Draw(self.img)

    def text(self, x: int, y: int, s: str, size: int, kind: str = "latin", color=(20, 20, 30), align: str = "left", lang: str = "und"):
        font = _font("arabic" if _is_arabic(s) else kind, size)
        vis, kw = _shape(s)
        bbox = self.draw.textbbox((0, 0), vis, font=font, **kw)
        tw = bbox[2] - bbox[0]
        if align == "right":
            x = x - tw
        elif align == "center":
            x = x - tw // 2
        self.draw.text((x - bbox[0], y - bbox[1]), vis, font=font, fill=color, **kw)
        self.lines.append({"text": s, "bbox": [x, y, tw, bbox[3] - bbox[1]], "language": lang, "script": "Arab" if _is_arabic(s) else "Latn"})


# ------------------------------------------------------------------ fictitious data
FR_PEOPLE = [("Hélène", "DUPONT"), ("Karim", "BENNANI"), ("Sophie", "MARTIN"), ("Youssef", "EL AMRANI"), ("Claire", "FONTAINE")]
EN_PEOPLE = [("James", "Carter"), ("Emily", "Walsh"), ("Omar", "Haddad"), ("Laura", "Bennett")]
AR_PEOPLE = ["كريم بناني", "يوسف العمراني", "سلمى الإدريسي", "هيلين دوبون", "عمر حداد", "ليلى المنصوري"]
PROFILES = [
    {"fr": "Cardiologue", "en": "Cardiologist", "ar": "طبيب أخصائي أمراض القلب", "company_fr": "Clinique Les Orangers", "company_en": "Orangers Clinic", "company_ar": "مصحة البرتقال", "industry": "healthcare", "domain": "orangers-clinic.ma", "honorific": "Dr."},
    {"fr": "Ingénieur Civil", "en": "Civil Engineer", "ar": "مهندس مدني", "company_fr": "Atlas Structures SARL", "company_en": "Atlas Structures Ltd", "company_ar": "شركة أطلس للهياكل", "industry": "engineering", "domain": "atlas-structures.ma", "honorific": None},
    {"fr": "Responsable Commercial", "en": "Sales Manager", "ar": "مدير المبيعات", "company_fr": "Groupe Medina Distribution", "company_en": "Medina Distribution Group", "company_ar": "مجموعة المدينة للتوزيع", "industry": "commerce", "domain": "medina-distribution.com", "honorific": None},
    {"fr": "Avocat au Barreau de Rabat", "en": "Lawyer", "ar": "محامي", "company_fr": "Cabinet Alaoui & Associés", "company_en": "Alaoui & Partners Law Firm", "company_ar": "مكتب العلوي للمحاماة", "industry": "legal", "domain": "alaoui-avocats.ma", "honorific": "Me"},
    {"fr": "Professeur", "en": "Professor", "ar": "أستاذ", "company_fr": "Université Hassan II", "company_en": "Hassan II University", "company_ar": "جامعة الحسن الثاني", "industry": "education", "domain": "univh2c.ma", "honorific": "Pr."},
]
ADDRESSES = [
    {"fr": ["25, Rue Ibn Battouta", "20250 Casablanca", "Maroc"], "ar": ["25 شارع ابن بطوطة", "الدار البيضاء 20250", "المغرب"], "en": ["25 Ibn Battouta Street", "20250 Casablanca", "Morocco"], "postal_code": "20250", "city": "Casablanca", "country": "MA"},
    {"fr": ["12 Avenue Mohammed V", "10000 Rabat", "Maroc"], "ar": ["12 شارع محمد الخامس", "الرباط 10000", "المغرب"], "en": ["12 Mohammed V Avenue", "10000 Rabat", "Morocco"], "postal_code": "10000", "city": "Rabat", "country": "MA"},
    {"fr": ["8 rue de la Paix", "75002 Paris", "France"], "ar": ["8 شارع السلام", "باريس 75002", "فرنسا"], "en": ["8 rue de la Paix", "75002 Paris", "France"], "postal_code": "75002", "city": "Paris", "country": "FR"},
]


def _phone(rng: random.Random, kind: str) -> tuple[str, str]:
    if kind == "mobile":
        digits = f"6{rng.randint(10, 99)}{rng.randint(100000, 999999)}"
    else:
        digits = f"522{rng.randint(100000, 999999)}"
    pretty = f"+212 {digits[0]} {digits[1:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]}"
    return pretty, f"+212{digits}"


def _slug(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def business_card(rng: random.Random, langs: str, idx: int) -> tuple[dict, dict[str, Image.Image]]:
    prof = rng.choice(PROFILES)
    addr = rng.choice(ADDRESSES)
    main = "en" if langs in ("en", "ar_en") else "fr"
    first, last = rng.choice(FR_PEOPLE if main == "fr" else EN_PEOPLE)
    ar_name = rng.choice(AR_PEOPLE)
    mob_pretty, mob_e164 = _phone(rng, "mobile")
    tel_pretty, tel_e164 = _phone(rng, "fixed")
    email = f"{_slug(first)[0]}.{_slug(last)}@{prof['domain']}"
    website = f"www.{prof['domain']}"
    c = Canvas(1050, 600)
    # brand patch as a stand-in logo
    c.draw.rectangle([40, 40, 140, 140], fill=(rng.randint(0, 80), rng.randint(60, 160), rng.randint(120, 220)))
    fields: dict = {"emails": [email], "website": "https://" + website, "phones": [mob_e164, tel_e164], "industry": prof["industry"]}
    y = 60
    if langs != "ar":
        name_line = (prof["honorific"] + " " if prof["honorific"] and main == "fr" else "") + f"{first} {last}"
        c.text(170, y, name_line, 46, "latin_bold", lang=main)
        fields.update({"full_name": f"{first} {last}", "first_name": first, "last_name": last})
        y += 70
        c.text(170, y, prof[main], 30, lang=main)
        fields["job_title"] = prof[main]
        y += 55
        company_lang = "en" if langs == "fr_en" else main
        c.text(170, y, prof[f"company_{company_lang}"], 30, "latin_bold", color=(40, 60, 120), lang=company_lang)
        fields["company"] = prof[f"company_{company_lang}"]
    if "ar" in langs:
        c.text(1010, 60 if langs == "ar" else 330, ar_name, 40, align="right", lang="ar")
        fields["arabic_name"] = ar_name
        if langs == "ar":
            fields["full_name"] = ar_name
            c.text(1010, 130, prof["ar"], 30, align="right", lang="ar")
            c.text(1010, 185, prof["company_ar"], 30, align="right", lang="ar")
            fields["job_title"] = prof["ar"]
            fields["company"] = prof["company_ar"]
    label_m, label_t = {"fr": ("Mob :", "Tél :"), "en": ("Mobile:", "Tel:")}["en" if langs == "fr_en" else main]
    y = 400
    c.text(60, y, f"{label_m} {mob_pretty}", 26, lang=main)
    c.text(60, y + 40, f"{label_t} {tel_pretty}", 26, lang=main)
    c.text(60, y + 80, email, 26)
    c.text(60, y + 120, website, 26)
    addr_lines = addr["ar"] if langs == "ar" else addr[main]
    ay = 400
    for line in addr_lines:
        c.text(1010, ay, line, 24, align="right", lang="ar" if langs == "ar" else main)
        ay += 38
    fields["address"] = {"postal_code": addr["postal_code"], "city": addr["city"] if langs != "ar" else None, "country_iso": addr["country"]}
    fields["phone_types"] = {mob_e164: "mobile", tel_e164: "phone"}
    ann = {"id": f"bc-{langs}-{idx:03d}", "product": "business_card", "source": "synthetic", "license": "generated, CC0", "languages": langs, "sides": {"front": {"lines": c.lines}}, "fields": fields, "tags": [f"lang:{langs}", "printed"]}
    return ann, {"front": c.img}


def degrade(img: Image.Image, kind: str, rng: random.Random) -> Image.Image:
    if kind == "rotated":
        return img.rotate(rng.choice([-7, -4, 4, 7]), expand=True, fillcolor=(200, 200, 200))
    if kind == "rotated90":
        return img.rotate(90, expand=True)
    if kind == "low_res":
        w, h = img.size
        return img.resize((w // 3, h // 3), Image.BILINEAR)
    if kind == "blur":
        return img.filter(ImageFilter.GaussianBlur(2.2))
    if kind == "noisy":
        import numpy as np

        arr = np.asarray(img).astype("int16")
        arr = arr + np.random.default_rng(rng.randint(0, 99999)).normal(0, 22, arr.shape).astype("int16")
        return Image.fromarray(arr.clip(0, 255).astype("uint8"))
    if kind == "faded":
        import numpy as np

        arr = np.asarray(img).astype("float32")
        arr = 255 - (255 - arr) * 0.35
        arr[..., 2] *= 0.85  # yellowing
        return Image.fromarray(arr.clip(0, 255).astype("uint8"))
    if kind == "photo":
        # card photographed on a desk: perspective + background
        bgc = Image.new("RGB", (int(img.width * 1.4), int(img.height * 1.5)), (70, 60, 50))
        bgc.paste(img, (int(img.width * 0.2), int(img.height * 0.25)))
        coeffs = _perspective_coeffs(bgc.size, rng)
        return bgc.transform(bgc.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=(70, 60, 50))
    return img


def _perspective_coeffs(size, rng):
    import numpy as np

    w, h = size
    d = 0.05
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [(rng.uniform(0, d) * w, rng.uniform(0, d) * h), (w - rng.uniform(0, d) * w, rng.uniform(0, d) * h), (w - rng.uniform(0, d) * w, h - rng.uniform(0, d) * h), (rng.uniform(0, d) * w, h - rng.uniform(0, d) * h)]
    A, B = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0, -x * u, -x * v])
        A.append([0, 0, 0, u, v, 1, -y * u, -y * v])
        B.extend([x, y])
    return np.linalg.solve(np.array(A, dtype=float), np.array(B, dtype=float)).tolist()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ml/datasets/synthetic/out")
    ap.add_argument("--n", type=int, default=3, help="samples per language combination")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--degradations", default="clean,rotated,low_res,noisy,photo,faded")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    degs = args.degradations.split(",")

    def save(ann, imgs, deg):
        sid = f"{ann['id']}-{deg}"
        d = out / sid
        d.mkdir(exist_ok=True)
        entry = json.loads(json.dumps(ann))
        entry["id"] = sid
        entry["tags"] = ann["tags"] + [f"quality:{deg}"]
        for side, im in imgs.items():
            im2 = degrade(im, deg, rng)
            p = d / f"{side}.jpg"
            im2.save(p, quality=90)
            entry["sides"][side]["image"] = f"{sid}/{side}.jpg"
            if deg != "clean":
                entry["sides"][side]["bbox_valid"] = False  # geometry changed; text GT still valid
        (d / "annotation.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append(entry["id"])

    for combo in ("fr", "en", "ar", "ar_fr", "ar_en", "fr_en"):
        for i in range(args.n):
            ann, imgs = business_card(rng, combo, i)
            for deg in degs:
                save(ann, imgs, deg)
    (out / "manifest.json").write_text(json.dumps({"source": "synthetic", "samples": manifest}, indent=2), encoding="utf-8")
    print(f"wrote {len(manifest)} samples to {out}")


if __name__ == "__main__":
    main()
