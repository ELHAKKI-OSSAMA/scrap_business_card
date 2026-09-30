"""Script and language identification plus language-aware normalization.

Deterministic by design: business-card lines are too short for
statistical language ID, so we report ``und`` (undetermined) instead of guessing.
"""

from language_detection.detect import (
    LanguageGuess,
    detect_line_language,
    detect_script,
    direction_for,
    script_counts,
    summarize_languages,
)
from language_detection.normalize import (
    PERSIAN_CODEPOINTS,
    digits_to_ascii,
    has_persian_codepoints,
    normalize_display,
    normalize_search,
    strip_arabic_diacritics,
)

__all__ = [
    "LanguageGuess",
    "detect_line_language",
    "detect_script",
    "direction_for",
    "script_counts",
    "summarize_languages",
    "PERSIAN_CODEPOINTS",
    "digits_to_ascii",
    "has_persian_codepoints",
    "normalize_display",
    "normalize_search",
    "strip_arabic_diacritics",
]
