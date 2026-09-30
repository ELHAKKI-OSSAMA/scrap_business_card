"""Postal code patterns. A 5-digit number alone is ambiguous (FR, MA, DZ, TN(4), US …), so the
country is reported only when the text contains supporting evidence (country or city name)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from language_detection import digits_to_ascii, normalize_search

POSTAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "5digit": re.compile(r"(?<![\d+])\d{5}(?![\d])"),
    "4digit": re.compile(r"(?<![\d+])\d{4}(?![\d])"),
    "UK": re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b"),
    "CA": re.compile(r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b"),
    "US": re.compile(r"\b\d{5}-\d{4}\b"),
}

COUNTRY_NAMES: dict[str, str] = {
    # normalized-search form -> ISO code
    "maroc": "MA", "morocco": "MA", "المغرب": "MA", "المملكة المغربية": "MA",
    "france": "FR", "فرنسا": "FR",
    "algerie": "DZ", "algeria": "DZ", "الجزائر": "DZ",
    "tunisie": "TN", "tunisia": "TN", "تونس": "TN",
    "egypte": "EG", "egypt": "EG", "مصر": "EG",
    "belgique": "BE", "belgium": "BE", "suisse": "CH", "switzerland": "CH",
    "canada": "CA", "espagne": "ES", "spain": "ES", "united kingdom": "GB", "uk": "GB", "england": "GB",
    "royaume-uni": "GB", "usa": "US", "united states": "US", "etats-unis": "US",
    "saudi arabia": "SA", "arabie saoudite": "SA", "السعودية": "SA",
    "emirats arabes unis": "AE", "united arab emirates": "AE", "uae": "AE", "الامارات": "AE",
    "liban": "LB", "lebanon": "LB", "لبنان": "LB", "jordanie": "JO", "jordan": "JO", "الاردن": "JO",
    "qatar": "QA", "قطر": "QA",
}

KNOWN_CITIES: dict[str, str] = {
    "casablanca": "MA", "الدار البيضاء": "MA", "rabat": "MA", "الرباط": "MA", "marrakech": "MA", "مراكش": "MA",
    "fes": "MA", "fès": "MA", "فاس": "MA", "tanger": "MA", "tangier": "MA", "طنجة": "MA", "agadir": "MA",
    "اكادير": "MA", "meknes": "MA", "مكناس": "MA", "oujda": "MA", "وجدة": "MA", "tetouan": "MA", "تطوان": "MA",
    "kenitra": "MA", "القنيطرة": "MA", "el jadida": "MA", "الجديدة": "MA",
    "paris": "FR", "باريس": "FR", "ليون": "FR", "مرسيليا": "FR", "lyon": "FR", "marseille": "FR", "toulouse": "FR", "nice": "FR", "bordeaux": "FR", "lille": "FR",
    "nantes": "FR", "strasbourg": "FR", "montpellier": "FR",
    "alger": "DZ", "algiers": "DZ", "oran": "DZ", "وهران": "DZ", "tunis": "TN", "sfax": "TN", "صفاقس": "TN",
    "cairo": "EG", "le caire": "EG", "القاهرة": "EG", "alexandria": "EG", "الاسكندرية": "EG",
    "london": "GB", "londres": "GB", "manchester": "GB", "new york": "US", "montreal": "CA", "montréal": "CA",
    "bruxelles": "BE", "brussels": "BE", "geneve": "CH", "genève": "CH", "dubai": "AE", "دبي": "AE",
    "riyadh": "SA", "الرياض": "SA", "beyrouth": "LB", "beirut": "LB", "بيروت": "LB", "amman": "JO", "عمان": "JO",
    "doha": "QA", "الدوحة": "QA",
}


@dataclass
class PostalMatch:
    code: str
    pattern: str
    start: int
    end: int


def find_postal_codes(text: str) -> list[PostalMatch]:
    s = digits_to_ascii(text)
    out: list[PostalMatch] = []
    taken: list[tuple[int, int]] = []
    for name in ("UK", "CA", "US", "5digit", "4digit"):
        for m in POSTAL_PATTERNS[name].finditer(s):
            if any(a <= m.start() < b for a, b in taken):
                continue
            out.append(PostalMatch(m.group(0), name, m.start(), m.end()))
            taken.append(m.span())
    return out


def find_country(text: str) -> tuple[str, str] | None:
    """Return (surface text, ISO code) of an explicit country mention."""
    key = normalize_search(text)
    for name in sorted(COUNTRY_NAMES, key=len, reverse=True):
        n = normalize_search(name)
        if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", key):
            return name, COUNTRY_NAMES[name]
    return None


def find_city(text: str) -> tuple[str, str] | None:
    key = normalize_search(text)
    for name in sorted(KNOWN_CITIES, key=len, reverse=True):
        n = normalize_search(name)
        m = re.search(rf"(?<!\w){re.escape(n)}(?!\w)", key)
        if m:
            return name, KNOWN_CITIES[name]
    return None
