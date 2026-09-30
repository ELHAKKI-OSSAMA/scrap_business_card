"""Deterministic validation for phones, emails and URLs.

Phone policy (spec §5):
* the original string is always kept;
* E.164 is stored only when the number carries an explicit international prefix, or when a
  default region was *explicitly configured* by the workspace/user and the number validates;
* the country is never inferred from the language of the card.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import phonenumbers
from email_validator import EmailNotValidError, validate_email

from language_detection import digits_to_ascii

# permissive candidate finders; validation happens afterwards
PHONE_CANDIDATE = re.compile(r"(?:(?:\+|00)\s?\d[\d\s().\-/]{6,}\d|\(?0\d[\d\s().\-/]{6,}\d)")
EMAIL_CANDIDATE = re.compile(r"[A-Za-z0-9._%+\-]+\s?@\s?[A-Za-z0-9.\-]+\s?\.\s?[A-Za-z]{2,}")
URL_CANDIDATE = re.compile(
    r"(?:(?:https?://)|(?:www\.))[^\s,;]+|\b[a-z0-9\-]+(?:\.[a-z0-9\-]+)*\.(?:com|net|org|ma|fr|dz|tn|eg|sa|ae|qa|uk|co|io|info|biz|edu|gov|be|ch|ca|de|es|it|us|lb|jo)\b(?:/[^\s,;]*)?",
    re.IGNORECASE,
)


_HOST = re.compile(r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$", re.IGNORECASE)


def is_safe_url(raw: str) -> bool:
    try:
        parts = urlsplit(raw.strip())
    except ValueError:
        return False
    if parts.scheme not in ("http", "https"):
        return False
    if parts.username or parts.password:
        return False
    host = parts.hostname or ""
    if not _HOST.match(host):
        return False
    return not any(ch in raw for ch in ("\n", "\r", "\t", " ", "<", ">", '"'))



@dataclass
class ParsedPhone:
    original: str
    e164: str | None
    region: str | None
    region_inferred_from: str  # explicit_prefix | default_region | none
    is_valid: bool
    number_type: str | None  # MOBILE / FIXED_LINE / ...


def parse_phone(raw: str, default_region: str | None = None) -> ParsedPhone:
    text = digits_to_ascii(raw).strip()
    text = re.sub(r"^00", "+", re.sub(r"\s+", " ", text))
    explicit = text.startswith("+")
    region_used = None if explicit else (default_region.upper() if default_region else None)
    try:
        num = phonenumbers.parse(text, region_used)
    except phonenumbers.NumberParseException:
        return ParsedPhone(raw, None, None, "none", False, None)
    valid = phonenumbers.is_valid_number(num)
    region = phonenumbers.region_code_for_number(num) if valid else None
    ntype = None
    if valid:
        t = phonenumbers.number_type(num)
        ntype = {
            phonenumbers.PhoneNumberType.MOBILE: "MOBILE",
            phonenumbers.PhoneNumberType.FIXED_LINE: "FIXED_LINE",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
            phonenumbers.PhoneNumberType.VOIP: "VOIP",
            phonenumbers.PhoneNumberType.TOLL_FREE: "TOLL_FREE",
        }.get(t, "OTHER")
    e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164) if valid else None
    return ParsedPhone(
        original=raw,
        e164=e164,
        region=region,
        region_inferred_from=("explicit_prefix" if explicit else "default_region") if valid else "none",
        is_valid=valid,
        number_type=ntype,
    )


def validate_email_address(raw: str) -> tuple[str | None, str | None]:
    """Return (normalized_email, error). Syntax only – no DNS lookups (privacy, offline)."""
    candidate = re.sub(r"\s+", "", raw).strip(".,;:()[]<>")
    try:
        res = validate_email(candidate, check_deliverability=False)
    except EmailNotValidError as exc:
        return None, str(exc)
    return res.normalized, None


def normalize_url(raw: str) -> str | None:
    s = raw.strip().rstrip(".,;:)")
    if not re.match(r"^https?://", s, re.IGNORECASE):
        s = "https://" + s
    try:
        parts = urlsplit(s)
    except ValueError:
        return None
    if not parts.hostname:
        return None
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def validate_url(raw: str) -> tuple[str | None, str | None]:
    norm = normalize_url(raw)
    if norm is None or not is_safe_url(norm):
        return None, "invalid_url"
    return norm, None
