from __future__ import annotations

import pytest

from language_detection import (
    detect_line_language,
    detect_script,
    digits_to_ascii,
    direction_for,
    has_persian_codepoints,
    normalize_display,
    normalize_search,
    summarize_languages,
)
from shared_types import Direction, Script


@pytest.mark.parametrize(
    "text,script",
    [
        ("الدكتورة هيلين دوبون", Script.arabic),
        ("Dr. Hélène Dupont", Script.latin),
        ("+212 6 12 34 56 78", Script.common),
        ("٠٦١٢٣٤٥٦٧٨", Script.common),  # Arabic-Indic digits are digits, not letters
        ("شركة Atlas Structures SARL", Script.mixed),
        ("", Script.unknown),
    ],
)
def test_detect_script(text, script):
    assert detect_script(text) == script


def test_mixed_line_direction_follows_majority():
    assert direction_for(Script.mixed, "شارع محمد الخامس Casablanca") == Direction.rtl
    assert direction_for(Script.mixed, "Clinique Les Orangers مصحة") == Direction.ltr


@pytest.mark.parametrize(
    "text,lang",
    [
        ("Chère Maman, il fait très beau ici", "fr"),
        ("Dear Mum, the weather is lovely here", "en"),
        ("Responsable Commercial", "fr"),
        ("Sales Manager", "en"),
        ("أمي العزيزة", "ar"),
        ("Rabat", "und"),  # a lone proper noun is not evidence of a language
        ("10000", "und"),
    ],
)
def test_line_language(text, lang):
    assert detect_line_language(text).language == lang


def test_und_confidence_is_none_without_evidence():
    g = detect_line_language("Casablanca")
    assert g.language == "und" and g.confidence is None


def test_document_is_not_single_language(page_factory):
    from shared_types import Side

    page = page_factory(Side.front, [("Dr. Hélène Dupont - Cardiologue", (10, 10, 500, 40)), ("الدكتورة هيلين دوبون", (10, 60, 400, 40)), ("Sales Manager", (10, 110, 300, 40))])
    regions = summarize_languages(page.lines)
    langs = {r.language for r in regions}
    assert {"fr", "ar", "en"} <= langs
    assert abs(sum(r.share for r in regions) - 1) < 0.01


# ------------------------------------------------------------------ normalization
def test_display_normalization_preserves_diacritics_and_accents():
    assert normalize_display("مُحَمَّد") == "مُحَمَّد"  # tashkeel kept
    assert normalize_display("Hélène  L'Écuyer-Dupont") == "Hélène L'Écuyer-Dupont"
    assert normalize_display("Chère   Maman") == "Chère Maman"


def test_tatweel_and_persian_codepoints():
    assert normalize_display("محـــمد") == "محمد"
    persian = "علی کریمی"  # FARSI YEH / KEHEH
    assert has_persian_codepoints(persian)
    out = normalize_display(persian)
    assert out == "علي كريمي"
    assert not has_persian_codepoints(out)
    # Maghrebi letters are NOT folded (legit in names like ڤ)
    assert normalize_display("ڤيكتور") == "ڤيكتور"


def test_normalization_does_not_touch_digits_in_display():
    assert normalize_display("هاتف ٠٦١٢") == "هاتف ٠٦١٢"


def test_arabic_numerals_to_ascii():
    assert digits_to_ascii("٠٦١٢٣٤٥٦٧٨") == "0612345678"
    assert digits_to_ascii("۰۱۲۳۴۵۶۷۸۹") == "0123456789"  # Persian/Urdu digits
    assert digits_to_ascii("Tél: ٠٥ 22") == "Tél: 05 22"


def test_search_key_folding():
    assert normalize_search("Université") == normalize_search("UNIVERSITE")
    assert normalize_search("أحمد") == normalize_search("احمد")
    assert normalize_search("مُحَمَّد") == normalize_search("محمد")
    assert normalize_search("٢٠٢٥٠") == "20250"
    # Arabic letters survive the Latin accent stripping
    assert normalize_search("الدار البيضاء") == "الدار البيضاء"
