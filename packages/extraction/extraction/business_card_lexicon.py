"""Business-card vocabulary additions (specialties, descriptions, extra titles).

Every entry is matched against text that is actually printed on the card; nothing here is used to
invent values. Canonical keys are English and stored as ``normalized_value`` only.
"""

from __future__ import annotations

import re

from language_detection import normalize_search

# explicit specialty terms -> canonical key. Matched accent/case-insensitively on whole words.
SPECIALTIES: dict[str, str] = {
    # hepato-gastroenterology
    "hépato-gastroentérologie": "hepato-gastroenterology", "hepato-gastroenterologie": "hepato-gastroenterology",
    "hépato gastro entérologie": "hepato-gastroenterology", "hepatogastroenterologie": "hepato-gastroenterology",
    "hepato-gastroenterology": "hepato-gastroenterology", "hepatogastroenterology": "hepato-gastroenterology",
    "gastro-entérologie": "gastroenterology", "gastroentérologie": "gastroenterology", "gastroenterology": "gastroenterology",
    "hépatologie": "hepatology", "hepatology": "hepatology",
    "أمراض الكبد والجهاز الهضمي": "hepato-gastroenterology", "أمراض الجهاز الهضمي": "gastroenterology",
    # other medical specialties
    "cardiologie": "cardiology", "cardiology": "cardiology", "أمراض القلب": "cardiology",
    "dermatologie": "dermatology", "dermatology": "dermatology", "الأمراض الجلدية": "dermatology",
    "pédiatrie": "pediatrics", "pediatrics": "pediatrics", "طب الأطفال": "pediatrics",
    "gynécologie": "gynecology", "gynécologie-obstétrique": "obstetrics-gynecology", "gynecology": "gynecology", "أمراض النساء": "gynecology",
    "ophtalmologie": "ophthalmology", "ophthalmology": "ophthalmology", "طب العيون": "ophthalmology",
    "oto-rhino-laryngologie": "otorhinolaryngology", "orl": "otorhinolaryngology",
    "rhumatologie": "rheumatology", "rheumatology": "rheumatology",
    "neurologie": "neurology", "neurology": "neurology",
    "pneumologie": "pulmonology", "pulmonology": "pulmonology",
    "urologie": "urology", "urology": "urology", "néphrologie": "nephrology", "nephrology": "nephrology",
    "endocrinologie": "endocrinology", "endocrinology": "endocrinology",
    "traumatologie-orthopédie": "orthopedics", "orthopédie": "orthopedics", "orthopedics": "orthopedics",
    "radiologie": "radiology", "radiology": "radiology", "psychiatrie": "psychiatry", "psychiatry": "psychiatry",
    "chirurgie dentaire": "dentistry", "médecine dentaire": "dentistry", "dentistry": "dentistry", "طب الأسنان": "dentistry",
    "orthodontie": "orthodontics", "orthodontics": "orthodontics",
    "kinésithérapie": "physiotherapy", "physiotherapy": "physiotherapy",
    "médecine générale": "general medicine", "general medicine": "general medicine", "الطب العام": "general medicine",
}

# lines that describe the professional scope rather than name a title
DESCRIPTION_PREFIXES = [
    "spécialiste", "specialiste", "specialist", "spécialisé", "specialise", "specialized", "specialised",
    "expert en", "expert in", "consultant en", "diplômé", "diplome", "lauréat", "laureat", "ancien interne",
    "ancien chef", "former", "أخصائي", "اختصاصي", "خبير",
]

# titles missing from the shared lexicon (checked in addition to it)
EXTRA_TITLES: dict[str, str | None] = {
    "chief executive officer": "business", "chief operating officer": "business", "chief financial officer": "finance",
    "chief technology officer": "technology", "chief marketing officer": "marketing", "cto": "technology", "cfo": "finance",
    "coo": "business", "managing director": "business", "managing partner": "business", "partner": "business",
    "président": "business", "president": "business", "vice president": "business", "vice-président": "business",
    "directeur général adjoint": "business", "head of": "business", "responsable": "business",
    "associé": "business", "associée": "business", "rais": None, "الرئيس المدير العام": "business",
}

MEDICAL_HONORIFICS = {"dr", "dr.", "docteur", "doctor", "pr", "pr.", "professeur", "الدكتور", "الدكتورة", "د"}
INFERRED_DOCTOR_TITLE = {"fr": "Médecin", "en": "Doctor", "ar": "طبيب"}

_SPECIALTY_KEYS = sorted(((normalize_search(k), v) for k, v in SPECIALTIES.items()), key=lambda kv: -len(kv[0]))


def find_specialty(text: str) -> tuple[str, str] | None:
    """Returns (printed span, canonical key) if an explicit specialty term is printed in ``text``."""
    norm = normalize_search(text).replace("’", "'")
    for key, canon in _SPECIALTY_KEYS:
        m = re.search(r"(?<![\w])" + re.escape(key) + r"(?![\w])", norm)
        if m:
            return text[m.start() : m.end()] if len(norm) == len(text) else key, canon
    return None


def is_description(text: str) -> bool:
    n = normalize_search(text)
    return any(n.startswith(normalize_search(p)) for p in DESCRIPTION_PREFIXES)


def match_extra_title(text: str) -> str | None:
    n = normalize_search(text)
    for k in sorted(EXTRA_TITLES, key=len, reverse=True):
        if re.search(r"(?<![\w])" + re.escape(normalize_search(k)) + r"(?![\w])", n):
            return k
    return None
