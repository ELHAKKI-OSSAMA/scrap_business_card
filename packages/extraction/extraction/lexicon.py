"""Multilingual keyword lexicons (Arabic / French / English).

Matching is done on ``normalize_search`` forms (accent-, case- and Arabic-diacritic-insensitive).
Lexicons only *label* text that is present on the card; they never add information."""

from __future__ import annotations

import re
from functools import lru_cache

from language_detection import normalize_search

# honorifics / civil titles (stripped from names, kept in original_value)
HONORIFICS = [
    "dr", "dr.", "pr", "pr.", "prof", "prof.", "professeur", "docteur", "me", "me.", "maître", "maitre",
    "m.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "mme", "mme.", "mlle", "mlle.", "miss", "monsieur", "madame",
    "mademoiselle", "eng.", "ing.", "sir",
    "الدكتور", "الدكتورة", "د.", "الأستاذ", "الأستاذة", "الاستاذ", "المهندس", "المهندسة", "م.", "السيد", "السيدة", "الآنسة",
]

# job titles -> (industry, specialty or None)
TITLES: dict[str, tuple[str | None, str | None]] = {
    # healthcare
    "médecin": ("healthcare", None), "medecin": ("healthcare", None), "doctor": ("healthcare", None),
    "physician": ("healthcare", None), "طبيب": ("healthcare", None), "طبيبة": ("healthcare", None),
    "cardiologue": ("healthcare", "cardiology"), "cardiologist": ("healthcare", "cardiology"), "أخصائي أمراض القلب": ("healthcare", "cardiology"),
    "pédiatre": ("healthcare", "pediatrics"), "pediatre": ("healthcare", "pediatrics"), "pediatrician": ("healthcare", "pediatrics"), "طب الأطفال": ("healthcare", "pediatrics"),
    "dentiste": ("healthcare", "dentistry"), "dentist": ("healthcare", "dentistry"), "chirurgien-dentiste": ("healthcare", "dentistry"), "طبيب أسنان": ("healthcare", "dentistry"),
    "chirurgien": ("healthcare", "surgery"), "surgeon": ("healthcare", "surgery"), "جراح": ("healthcare", "surgery"),
    "gynécologue": ("healthcare", "gynecology"), "gynecologist": ("healthcare", "gynecology"),
    "dermatologue": ("healthcare", "dermatology"), "dermatologist": ("healthcare", "dermatology"),
    "ophtalmologue": ("healthcare", "ophthalmology"), "ophthalmologist": ("healthcare", "ophthalmology"),
    "radiologue": ("healthcare", "radiology"), "radiologist": ("healthcare", "radiology"),
    "pharmacien": ("healthcare", "pharmacy"), "pharmacienne": ("healthcare", "pharmacy"), "pharmacist": ("healthcare", "pharmacy"), "صيدلي": ("healthcare", "pharmacy"),
    "infirmier": ("healthcare", "nursing"), "infirmière": ("healthcare", "nursing"), "nurse": ("healthcare", "nursing"), "ممرض": ("healthcare", "nursing"),
    "kinésithérapeute": ("healthcare", "physiotherapy"), "physiotherapist": ("healthcare", "physiotherapy"),
    "médecine générale": ("healthcare", "general medicine"), "general practitioner": ("healthcare", "general medicine"), "طب عام": ("healthcare", "general medicine"),
    # engineering
    "ingénieur": ("engineering", None), "ingenieur": ("engineering", None), "engineer": ("engineering", None), "مهندس": ("engineering", None), "مهندسة": ("engineering", None),
    "ingénieur civil": ("engineering", "civil engineering"), "civil engineer": ("engineering", "civil engineering"), "مهندس مدني": ("engineering", "civil engineering"),
    "ingénieur logiciel": ("engineering", "software engineering"), "software engineer": ("engineering", "software engineering"),
    "ingénieur électricien": ("engineering", "electrical engineering"), "electrical engineer": ("engineering", "electrical engineering"),
    "ingénieur mécanique": ("engineering", "mechanical engineering"), "mechanical engineer": ("engineering", "mechanical engineering"),
    "architecte": ("engineering", "architecture"), "architect": ("engineering", "architecture"), "مهندس معماري": ("engineering", "architecture"),
    "développeur": ("technology", "software development"), "developer": ("technology", "software development"), "مطور": ("technology", "software development"),
    # commerce / management
    "directeur": ("business", None), "directrice": ("business", None), "director": ("business", None), "مدير": ("business", None), "مديرة": ("business", None),
    "directeur général": ("business", None), "general manager": ("business", None), "ceo": ("business", None), "pdg": ("business", None), "المدير العام": ("business", None),
    "gérant": ("business", None), "gerant": ("business", None), "manager": ("business", None),
    "commercial": ("commerce", "sales"), "sales manager": ("commerce", "sales"), "sales representative": ("commerce", "sales"),
    "responsable commercial": ("commerce", "sales"), "chargé d'affaires": ("commerce", "sales"), "account manager": ("commerce", "sales"),
    "مسؤول المبيعات": ("commerce", "sales"), "مدير المبيعات": ("commerce", "sales"), "مندوب مبيعات": ("commerce", "sales"),
    "comptable": ("finance", "accounting"), "accountant": ("finance", "accounting"), "محاسب": ("finance", "accounting"),
    "consultant": ("business", "consulting"), "consultante": ("business", "consulting"), "مستشار": ("business", "consulting"),
    "chef de projet": ("business", "project management"), "project manager": ("business", "project management"), "مدير مشروع": ("business", "project management"),
    "fondateur": ("business", None), "founder": ("business", None), "co-founder": ("business", None), "مؤسس": ("business", None),
    # education
    "professeur": ("education", None), "professor": ("education", None), "enseignant": ("education", None), "enseignante": ("education", None),
    "teacher": ("education", None), "lecturer": ("education", None), "maître de conférences": ("education", None),
    "أستاذ": ("education", None), "أستاذة": ("education", None), "استاذ": ("education", None), "معلم": ("education", None), "معلمة": ("education", None),
    "doyen": ("education", None), "dean": ("education", None), "عميد": ("education", None), "chercheur": ("education", "research"), "researcher": ("education", "research"), "باحث": ("education", "research"),
    # legal
    "avocat": ("legal", None), "avocate": ("legal", None), "lawyer": ("legal", None), "attorney": ("legal", None), "solicitor": ("legal", None), "barrister": ("legal", None),
    "محامي": ("legal", None), "محام": ("legal", None), "محامية": ("legal", None), "notaire": ("legal", "notary"), "notary": ("legal", "notary"), "موثق": ("legal", "notary"),
    "avocat au barreau": ("legal", None), "juriste": ("legal", None), "legal counsel": ("legal", None), "مستشار قانوني": ("legal", None),
    "huissier": ("legal", "bailiff"), "عدل": ("legal", "notary"),
}

COMPANY_MARKERS = [
    "sarl", "s.a.r.l", "sa", "s.a.", "sas", "law firm", "firm", "partners", "associates", "associés", "associes", "avocats associés", "sarlau", "ltd", "ltd.", "limited", "inc", "inc.", "llc", "plc", "gmbh", "group", "groupe",
    "holding", "company", "corporation", "corp", "co.", "& co", "cabinet", "clinique", "clinic", "hôpital", "hopital", "hospital",
    "laboratoire", "laboratory", "université", "universite", "university", "école", "ecole", "school", "institut", "institute",
    "faculté", "faculty", "consulting", "technologies", "solutions", "services", "industries", "bank", "banque", "assurances",
    "شركة", "مؤسسة", "مجموعة", "مكتب", "مصحة", "مستشفى", "عيادة", "جامعة", "مدرسة", "معهد", "كلية", "بنك", "مختبر",
]

DEPARTMENT_MARKERS = [
    "department", "dept", "département", "departement", "service", "division", "direction", "pôle", "unit",
    "قسم", "إدارة", "ادارة", "مصلحة", "شعبة",
]

QUALIFICATION_PATTERNS = [
    r"\bph\.?\s?d\.?\b", r"\bm\.?d\.?\b", r"\bmba\b", r"\bm\.?sc\.?\b", r"\bb\.?sc\.?\b", r"\bllm\b", r"\bll\.?b\.?\b",
    r"\bdocteur en [\w\s'’-]+", r"\bmaster en [\w\s'’-]+", r"\bmaster of [\w\s'’-]+", r"\bdiplômée? d[e'’] ?[\w\s'’-]+",
    r"\blauréate? de [\w\s'’-]+", r"\bingénieur d['’]état\b", r"\bexpert[- ]comptable\b",
    r"دكتوراه(?:\s+في\s+[؀-ۿ\s]+)?", r"ماجستير(?:\s+في\s+[؀-ۿ\s]+)?", r"إجازة في [؀-ۿ\s]+", r"دبلوم [؀-ۿ\s]+",
]
CERTIFICATION_PATTERNS = [
    r"\bpmp\b", r"\bcpa\b", r"\bcfa\b", r"\bacca\b", r"\bcissp\b", r"\bcisa\b", r"\bitil\b", r"\bprince2\b",
    r"\biso\s?\d{4,5}(?::\d{4})?\b", r"\bcertifi(?:ed|é|ée)\s[\w\s'’-]+", r"\baws certified[\w\s-]*", r"معتمد(?:ة)?(?:\s+[؀-ۿ]+)*",
]
MEMBERSHIP_PATTERNS = [
    r"\bmembre (?:de|du|des) [\w\s'’-]+", r"\bmember of [\w\s'’-]+", r"\bordre (?:national )?des [\w\s'’-]+",
    r"\binscrite? au barreau (?:de|d['’]) ?[\w\s'’-]+", r"\bbarreau de [\w\s'’-]+", r"\b[\w\s]*bar association\b",
    r"\bfellow of [\w\s'’-]+", r"عضو (?:في )?[؀-ۿ\s]+", r"هيئة [؀-ۿ\s]+",
]

PHONE_LABELS: dict[str, list[str]] = {
    "whatsapp": ["whatsapp", "whats app", "wa", "واتساب", "واتس اب", "واتس"],
    "fax": ["fax", "télécopie", "telecopie", "télécopieur", "فاكس"],
    "mobile": ["mob", "mobile", "portable", "port", "gsm", "cell", "cellulaire", "جوال", "محمول", "نقال", "الهاتف المحمول"],
    "phone": ["tel", "tél", "téléphone", "telephone", "phone", "ph", "office", "bureau", "fixe", "standard", "هاتف", "الهاتف", "ت", "هـ"],
}

ADDRESS_MARKERS = [
    "rue", "avenue", "av", "av.", "bd", "bd.", "boulevard", "place", "impasse", "allée", "allee", "chemin", "route", "quartier",
    "lot", "lotissement", "résidence", "residence", "immeuble", "imm", "imm.", "étage", "etage", "appt", "apt", "bureau n",
    "bp", "b.p.", "cedex", "zone industrielle", "zi", "street", "st.", "road", "rd.", "lane", "suite", "floor", "building",
    "po box", "p.o. box", "square", "drive", "way",
    "شارع", "زنقة", "حي", "زقاق", "عمارة", "الطابق", "شقة", "رقم", "ص.ب", "صندوق البريد", "تجزئة", "إقامة", "اقامة", "طريق", "ساحة", "المنطقة الصناعية",
]


SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin", "twitter.com": "twitter", "x.com": "x", "facebook.com": "facebook", "fb.com": "facebook",
    "instagram.com": "instagram", "youtube.com": "youtube", "tiktok.com": "tiktok", "github.com": "github",
}


@lru_cache(maxsize=None)
def _compiled_terms(terms: tuple[str, ...]) -> re.Pattern[str]:
    parts = sorted({re.escape(normalize_search(t)) for t in terms}, key=len, reverse=True)
    return re.compile(r"(?<![\w])(" + "|".join(parts) + r")(?![\w])")


def find_terms(text: str, terms: list[str] | tuple[str, ...]) -> list[str]:
    """Return matched lexicon terms (in normalized form) found in ``text``."""
    return [m.group(1) for m in _compiled_terms(tuple(terms)).finditer(normalize_search(text))]


def has_term(text: str, terms: list[str] | tuple[str, ...]) -> bool:
    return bool(find_terms(text, terms))


_TITLE_KEYS = {normalize_search(k): v for k, v in TITLES.items()}


def match_titles(text: str) -> list[tuple[str, str | None, str | None]]:
    """[(matched_term, industry, specialty)] longest-first."""
    return [(t, *_TITLE_KEYS[t]) for t in find_terms(text, tuple(TITLES))]


def find_patterns(text: str, patterns: list[str]) -> list[str]:
    out = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            s = m.group(0).strip(" ,;-–")
            if s and s not in out:
                out.append(s)
    return out
