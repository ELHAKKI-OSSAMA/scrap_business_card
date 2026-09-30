from __future__ import annotations

import pytest

from validation import is_safe_url, parse_phone, validate_email_address, validate_url
from validation.postal import find_city, find_country, find_postal_codes


def test_phone_with_explicit_prefix():
    p = parse_phone("+212 6 12 34 56 78")
    assert p.is_valid and p.e164 == "+212612345678" and p.region == "MA" and p.region_inferred_from == "explicit_prefix"


def test_phone_00_prefix_and_arabic_digits():
    assert parse_phone("00212 5 22 34 19 60").e164 == "+212522341960"
    assert parse_phone("+٢١٢ ٦ ١٢ ٣٤ ٥٦ ٧٨").e164 == "+212612345678"


def test_national_number_is_not_assigned_a_country_without_config():
    p = parse_phone("06 12 34 56 78")
    assert p.e164 is None and not p.is_valid and p.region_inferred_from == "none"
    q = parse_phone("06 12 34 56 78", default_region="FR")
    assert q.e164 == "+33612345678" and q.region_inferred_from == "default_region"


def test_original_phone_is_kept():
    raw = "+33 (0)1 42 68 53 00"
    assert parse_phone(raw).original == raw


@pytest.mark.parametrize("raw,ok", [("a.b@exemple.fr", True), ("contact @ clinique.ma", True), ("nope@", False), ("x@y", False)])
def test_email(raw, ok):
    norm, err = validate_email_address(raw)
    assert (err is None) == ok
    if ok:
        assert " " not in norm


@pytest.mark.parametrize(
    "url,safe",
    [
        ("https://www.univh2c.ma", True),
        ("http://example.com/a?b=c", True),
        ("javascript:alert(1)", False),
        ("https://user:pass@example.com", False),
        ("data:text/html;base64,PHNjcmlwdD4=", False),
        ("https://exa mple.com", False),
        ("ftp://example.com", False),
        ("https://localhost", False),
    ],
)
def test_url_safety(url, safe):
    assert is_safe_url(url) is safe


def test_validate_url_adds_scheme():
    assert validate_url("www.atlas-structures.ma")[0] == "https://www.atlas-structures.ma"
    assert validate_url("javascript:alert(1)")[0] is None


def test_postal_and_places():
    assert [m.code for m in find_postal_codes("20250 Casablanca")] == ["20250"]
    assert [m.code for m in find_postal_codes("London SW1A 1AA")] == ["SW1A 1AA"]
    assert find_city("الدار البيضاء 20250")[1] == "MA"
    assert find_country("12 rue X, 75002 Paris, FRANCE")[1] == "FR"
    assert find_country("Casablanca") is None  # a city is not a country mention
