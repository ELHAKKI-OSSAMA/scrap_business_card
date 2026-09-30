from __future__ import annotations

import re
from typing import Any, Iterable

from extraction.lexicon import ADDRESS_MARKERS, COMPANY_MARKERS, HONORIFICS, find_terms, has_term
from language_detection import detect_script, digits_to_ascii, normalize_display, normalize_search
from shared_types import Address, ExtractionMethod, FieldValue, OcrLine, OcrPage, ReviewStatus, Script
from validation import EMAIL_CANDIDATE, PHONE_CANDIDATE, URL_CANDIDATE, field_confidence
from validation.postal import find_city, find_country, find_postal_codes

REVIEW_THRESHOLD = 0.75


def review_status_for(conf: float | None) -> ReviewStatus:
    return ReviewStatus.needs_review if conf is None or conf < REVIEW_THRESHOLD else ReviewStatus.unreviewed


def make_field(
    value: Any,
    lines: Iterable[OcrLine],
    method: ExtractionMethod,
    *,
    validated: bool | None = None,
    original: str | None = None,
    normalized: Any = None,
    notes: str | None = None,
    force_review: bool = False,
) -> FieldValue:
    lines = list(lines)
    conf = field_confidence(lines, method.value, validated)
    status = ReviewStatus.needs_review if force_review else review_status_for(conf)
    return FieldValue(
        value=value,
        original_value=original if original is not None else (" ".join(l.text for l in lines) or None),
        normalized_value=normalized,
        confidence=conf,
        source_region_ids=[l.id for l in lines],
        extraction_method=method,
        review_status=status,
        notes=notes,
    )


def all_lines(pages: list[OcrPage]) -> list[OcrLine]:
    out: list[OcrLine] = []
    for p in sorted(pages, key=lambda p: 0 if p.side.value == "front" else 1):
        out.extend(sorted(p.lines, key=lambda l: l.line_index if l.line_index is not None else 0))
    return [l for l in out if l.text.strip()]


def contact_coverage(text: str) -> float:
    """Fraction of the line covered by e-mail/URL/phone matches (to skip pure-contact lines)."""
    s = digits_to_ascii(text)
    covered = 0
    for rx in (EMAIL_CANDIDATE, URL_CANDIDATE, PHONE_CANDIDATE):
        covered += sum(len(m.group(0)) for m in rx.finditer(s))
    stripped = len(re.sub(r"\s", "", s)) or 1
    return min(1.0, covered / stripped)


def strip_honorific(text: str) -> tuple[str, str | None]:
    s = text.strip()
    for h in sorted(HONORIFICS, key=len, reverse=True):
        pat = re.compile(rf"^{re.escape(h)}(?:\s+|(?<=\.))", re.IGNORECASE)
        m = pat.match(s)
        if m:
            return s[m.end():].strip(" .,:"), s[: m.end()].strip()
    return s, None


_NAME_TOKEN_LAT = re.compile(r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’\-.]*$")


def looks_like_name(text: str) -> bool:
    """Structural test only (token count, capitalisation, no digits/contact/company words)."""
    core, _ = strip_honorific(text)
    if not core or any(ch.isdigit() for ch in digits_to_ascii(core)) or "@" in core:
        return False
    if contact_coverage(core) > 0.3 or has_term(core, COMPANY_MARKERS) or has_term(core, ADDRESS_MARKERS):
        return False
    tokens = core.replace(",", " ").split()
    if not 2 <= len(tokens) <= 5:
        return False
    script = detect_script(core)
    if script == Script.latin:
        return all(_NAME_TOKEN_LAT.match(t) or t.lower() in {"de", "du", "la", "le", "van", "von", "el", "al", "ben", "ibn", "bin", "d'"} for t in tokens)
    if script == Script.arabic:
        return all(len(t) >= 2 for t in tokens) and len(core) <= 40
    return False


def split_latin_name(name: str) -> tuple[str | None, str | None, str]:
    """(first, last, rule). French convention: an ALL-CAPS token is the family name."""
    tokens = name.split()
    if len(tokens) < 2:
        return None, None, "single_token"
    caps = [t for t in tokens if t.isupper() and len(t) > 1]
    if caps and len(caps) < len(tokens):
        last = " ".join(caps)
        first = " ".join(t for t in tokens if t not in caps)
        return first, last, "uppercase_family_name"
    return " ".join(tokens[:-1]), tokens[-1], "last_token"


def line_flags(line: OcrLine) -> set[str]:
    return {f for alt in line.alternatives for f in alt.get("flags", [])}


def parse_address_block(lines: list[OcrLine], addr_id: str, role: str = "unknown", role_evidence: str | None = None, method: ExtractionMethod = ExtractionMethod.layout) -> Address:
    original = "\n".join(l.text for l in lines)
    normalized = "\n".join(normalize_display(l.text) for l in lines)
    postal = None
    city = None
    country = None
    street = None
    building = None
    digits_uncertain = any(line_flags(l) & {"digits_possibly_dropped"} for l in lines)
    for l in lines:
        t = l.text
        if postal is None:
            codes = [c for c in find_postal_codes(t) if c.pattern != "4digit" or has_term(t, ["cedex", "bp"]) or len(lines) > 1]
            # a 4/5-digit run in a street line ("25 rue …") is a house number, not a postal code
            codes = [c for c in codes if not (has_term(t, ADDRESS_MARKERS) and digits_to_ascii(t).strip().startswith(c.code))]
            if codes:
                postal = codes[-1].code
                if line_flags(l) & {"digits_possibly_dropped", "digits_repaired_by_segmentation"}:
                    digits_uncertain = True
        if city is None:
            c = find_city(t)
            if c:
                city = _surface(t, c[0])
        if country is None:
            c = find_country(t)
            if c:
                country = _surface(t, c[0])
        if street is None and has_term(t, ["rue", "avenue", "av", "bd", "boulevard", "street", "road", "lane", "chemin", "route", "impasse", "allée", "place", "drive", "شارع", "زنقة", "طريق", "زقاق", "ساحة"]):
            street = normalize_display(t)
        if building is None and has_term(t, ["immeuble", "imm", "résidence", "residence", "building", "bloc", "tour", "tower", "عمارة", "إقامة", "اقامة", "برج"]):
            building = normalize_display(t)
    if city is None and postal is not None:
        # "75008 Paris" – take the words right after the postal code on the same line
        for l in lines:
            s = digits_to_ascii(l.text)
            m = re.search(rf"{re.escape(postal)}\s+([^\d,]+)", s)
            if m:
                city = m.group(1).strip(" ,.-")
                break
    evidence_terms = sum(x is not None for x in (postal, city, country, street, building))
    conf = field_confidence(lines, method.value, validated=evidence_terms >= 2 or None)
    if digits_uncertain and conf is not None:
        conf = round(conf * 0.5, 3)  # the Arabic recognizer is unreliable on digit runs (see model-selection.md)
    return Address(
        id=addr_id,
        original_text=original,
        normalized_text=normalized,
        street=street,
        building=building,
        postal_code=postal,
        city=city,
        region=None,
        country=country,
        role=role,  # type: ignore[arg-type]
        role_evidence=role_evidence,
        confidence=conf,
        source_region_ids=[l.id for l in lines],
        extraction_method=method,
        review_status=review_status_for(conf),
    )


def _surface(text: str, name: str) -> str:
    """Return the matched span as written on the document (not the lexicon spelling)."""
    key = normalize_search(name)
    words = text.split()
    n = len(name.split())
    for i in range(len(words) - n + 1):
        cand = " ".join(words[i : i + n]).strip(",.;:-")
        if normalize_search(cand) == key:
            return cand
    return name


def address_score(text: str) -> int:
    score = 0
    if has_term(text, ADDRESS_MARKERS):
        score += 2
    if find_postal_codes(text):
        score += 1
    if find_city(text):
        score += 2
    if find_country(text):
        score += 2
    return score


def group_by_block(lines: list[OcrLine]) -> dict[tuple[str, int], list[OcrLine]]:
    blocks: dict[tuple[str, int], list[OcrLine]] = {}
    for l in lines:
        blocks.setdefault((l.side.value, l.block_index or 0), []).append(l)
    for v in blocks.values():
        v.sort(key=lambda l: l.line_index or 0)
    return blocks


__all__ = [
    "REVIEW_THRESHOLD",
    "make_field",
    "all_lines",
    "contact_coverage",
    "strip_honorific",
    "looks_like_name",
    "split_latin_name",
    "parse_address_block",
    "address_score",
    "group_by_block",
    "find_terms",
    "review_status_for",
]
