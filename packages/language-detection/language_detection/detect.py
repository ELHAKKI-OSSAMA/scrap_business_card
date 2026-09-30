from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from shared_types import Direction, LanguageRegion, OcrLine, Script

_ARABIC_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))
_ARABIC_DIGITS = set("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")


def _is_arabic_letter(ch: str) -> bool:
    cp = ord(ch)
    if ch in _ARABIC_DIGITS:
        return False
    return any(lo <= cp <= hi for lo, hi in _ARABIC_RANGES) and unicodedata.category(ch).startswith("L")


def _is_latin_letter(ch: str) -> bool:
    if not ch.isalpha():
        return False
    cp = ord(ch)
    return ch.isascii() or 0x00C0 <= cp <= 0x024F or 0x1E00 <= cp <= 0x1EFF


def script_counts(text: str) -> dict[str, int]:
    c = {"arabic": 0, "latin": 0, "digit": 0, "other_letter": 0}
    for ch in text:
        if _is_arabic_letter(ch):
            c["arabic"] += 1
        elif _is_latin_letter(ch):
            c["latin"] += 1
        elif ch.isdigit():
            c["digit"] += 1
        elif ch.isalpha():
            c["other_letter"] += 1
    return c


def detect_script(text: str) -> Script:
    c = script_counts(text)
    letters = c["arabic"] + c["latin"] + c["other_letter"]
    if letters == 0:
        return Script.common if text.strip() else Script.unknown
    if c["arabic"] and c["latin"]:
        minority = min(c["arabic"], c["latin"]) / letters
        if minority >= 0.15:
            return Script.mixed
        return Script.arabic if c["arabic"] > c["latin"] else Script.latin
    if c["arabic"]:
        return Script.arabic
    if c["latin"]:
        return Script.latin
    return Script.unknown


def direction_for(script: Script, text: str = "") -> Direction:
    if script == Script.arabic:
        return Direction.rtl
    if script == Script.mixed:
        c = script_counts(text)
        return Direction.rtl if c["arabic"] >= c["latin"] else Direction.ltr
    return Direction.ltr


# --- French vs English ---------------------------------------------------------------

_FR_WORDS = {
    "le", "la", "les", "de", "des", "du", "et", "à", "au", "aux", "pour", "avec", "sur", "dans", "en",
    "un", "une", "est", "je", "vous", "nous", "mon", "ma", "mes", "ton", "votre", "cher", "chère",
    "chers", "bonjour", "bisous", "amitiés", "baisers", "merci", "rue", "avenue", "av", "bd", "boulevard",
    "chemin", "impasse", "allée", "quartier", "résidence", "immeuble", "étage", "appt", "bp", "cedex",
    "madame", "monsieur", "mme", "mlle", "mr", "directeur", "directrice", "ingénieur", "médecin",
    "docteur", "avocat", "gérant", "chef", "responsable", "commercial", "société", "tél", "tel",
    "télécopie", "portable", "adresse", "courriel", "cabinet", "clinique", "maître", "professeur",
    "université", "école", "très", "bien", "bons", "baisers", "souvenirs", "ici", "temps", "beau",
}
_EN_WORDS = {
    "the", "and", "of", "to", "for", "with", "on", "in", "a", "an", "is", "i", "you", "we", "my", "your",
    "dear", "love", "hello", "regards", "best", "wishes", "from", "street", "st", "road", "rd", "lane",
    "suite", "floor", "apt", "building", "po", "box", "mr", "mrs", "ms", "director", "manager", "engineer",
    "doctor", "lawyer", "attorney", "senior", "head", "sales", "officer", "company", "phone", "mobile",
    "office", "address", "email", "university", "school", "weather", "here", "having", "great", "time",
    "wish", "were", "this", "that", "at", "by", "department",
}
_FR_CHARS = set("éèêëàâîïôûùüÿçœæÉÈÊÀÂÎÔÛÇŒ")
_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)


@dataclass(frozen=True)
class LanguageGuess:
    language: str  # ar | fr | en | und
    confidence: float | None
    script: Script


def _fr_en(text: str) -> tuple[str, float | None]:
    tokens = [t.casefold() for t in _TOKEN.findall(text)]
    fr = sum(1 for t in tokens if t in _FR_WORDS)
    en = sum(1 for t in tokens if t in _EN_WORDS)
    fr += 0.5 * sum(1 for ch in text if ch in _FR_CHARS)
    if "'" in text or "’" in text:
        # French elision (l', d', qu') vs English contractions ('s, n't)
        if re.search(r"\b(?:l|d|qu|j|n|s|c|m|t)['’]\w", text, re.IGNORECASE):
            fr += 1
        if re.search(r"\w['’](?:s|t|re|ll|ve|d)\b", text, re.IGNORECASE):
            en += 1
    total = fr + en
    if total < 1:
        return "und", None
    if fr == en:
        return "und", 0.5
    lang = "fr" if fr > en else "en"
    conf = max(fr, en) / total
    # dampen when evidence is thin: one weak cue should not look certain
    conf = round(conf * min(1.0, total / 3), 3)
    return lang, conf


def detect_line_language(text: str) -> LanguageGuess:
    script = detect_script(text)
    if script == Script.arabic:
        c = script_counts(text)
        conf = c["arabic"] / max(1, c["arabic"] + c["latin"] + c["other_letter"])
        return LanguageGuess("ar", round(conf, 3), script)
    if script == Script.latin:
        lang, conf = _fr_en(text)
        return LanguageGuess(lang, conf, script)
    if script == Script.mixed:
        c = script_counts(text)
        if c["arabic"] >= c["latin"]:
            return LanguageGuess("ar", round(c["arabic"] / (c["arabic"] + c["latin"]), 3), script)
        lang, conf = _fr_en(text)
        return LanguageGuess(lang, conf, script)
    return LanguageGuess("und", None, script)


def summarize_languages(lines: list[OcrLine]) -> list[LanguageRegion]:
    """Language share by recognized characters. A document is never labelled with a single
    language on the basis of one region: every (language, script) pair is reported."""
    buckets: dict[tuple[str, Script], list[str]] = {}
    chars: Counter[tuple[str, Script]] = Counter()
    for ln in lines:
        key = (ln.language, ln.script)
        buckets.setdefault(key, []).append(ln.id)
        chars[key] += len(ln.text.strip())
    total = sum(chars.values()) or 1
    regions = [
        LanguageRegion(language=k[0], script=k[1], line_ids=v, share=round(chars[k] / total, 3))
        for k, v in buckets.items()
    ]
    regions.sort(key=lambda r: -r.share)
    return regions
