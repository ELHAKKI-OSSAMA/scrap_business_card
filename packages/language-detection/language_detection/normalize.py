"""Language-aware normalization.

Rules:
* The original OCR string is never modified; these functions return new strings.
* ``normalize_display`` is conservative (safe to show as "normalized"): Unicode NFC,
  whitespace cleanup, Arabic tatweel removal, Persian yeh/keheh -> Arabic yeh/kaf.
  Diacritics, accents, apostrophes, hyphens and historical spellings are preserved.
* ``normalize_search`` is aggressive and only used for search keys / dedupe keys.
"""

from __future__ import annotations

import re
import unicodedata

TATWEEL = "ـ"
ARABIC_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")

# Persian/Urdu code points that the Arabic recognizer may emit for Arabic letters.
# Only yeh and keheh are mapped: they are visually identical to Arabic yeh/kaf in
# many fonts. پ چ ژ گ ڤ are *kept* because they legitimately appear in Maghrebi
# and transliterated names (e.g. ڤ for "V").
PERSIAN_TO_ARABIC = {
    "ی": "ي",  # ی FARSI YEH -> ي
    "ک": "ك",  # ک KEHEH     -> ك
}
PERSIAN_CODEPOINTS = frozenset(PERSIAN_TO_ARABIC)

_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})

_WS = re.compile(r"\s+")


def digits_to_ascii(text: str) -> str:
    """Map Arabic-Indic (U+0660..) and Extended Arabic-Indic (U+06F0..) digits to 0-9."""
    return text.translate(_DIGIT_MAP)


def has_persian_codepoints(text: str) -> bool:
    return any(ch in PERSIAN_CODEPOINTS for ch in text)


def strip_arabic_diacritics(text: str) -> str:
    return ARABIC_DIACRITICS.sub("", text)


def normalize_display(text: str) -> str:
    if not text:
        return ""
    out = unicodedata.normalize("NFC", text)
    out = out.replace(TATWEEL, "")
    out = "".join(PERSIAN_TO_ARABIC.get(ch, ch) for ch in out)
    # Arabic comma / semicolon are kept; only whitespace is collapsed.
    out = _WS.sub(" ", out).strip()
    return out


_ALEF_VARIANTS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})


def normalize_search(text: str) -> str:
    """Accent/diacritic-insensitive, case-folded key. Never shown as the value."""
    if not text:
        return ""
    out = normalize_display(text)
    out = strip_arabic_diacritics(out).translate(_ALEF_VARIANTS)
    out = digits_to_ascii(out)
    decomposed = unicodedata.normalize("NFKD", out)
    # remove Latin combining marks only (keeps Arabic letters intact)
    out = "".join(ch for ch in decomposed if not (unicodedata.combining(ch) and ord(ch) < 0x0600))
    out = unicodedata.normalize("NFC", out).casefold()
    out = re.sub(r"[’'`´]", "'", out)
    return _WS.sub(" ", out).strip()
