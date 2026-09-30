"""Rule + layout based business-card extraction (deterministic, offline)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import numpy as np

from document_preprocessing import detect_color_patches
from extraction.common import (
    address_score,
    all_lines,
    contact_coverage,
    group_by_block,
    looks_like_name,
    make_field,
    parse_address_block,
    split_latin_name,
    strip_honorific,
)
from extraction.business_card_lexicon import EXTRA_TITLES, INFERRED_DOCTOR_TITLE, MEDICAL_HONORIFICS, find_specialty, is_description, match_extra_title
from extraction.lexicon import (
    CERTIFICATION_PATTERNS,
    COMPANY_MARKERS,
    DEPARTMENT_MARKERS,
    MEMBERSHIP_PATTERNS,
    PHONE_LABELS,
    QUALIFICATION_PATTERNS,
    SOCIAL_DOMAINS,
    find_patterns,
    find_terms,
    has_term,
    match_titles,
)
from language_detection import detect_script, digits_to_ascii, normalize_display, normalize_search, summarize_languages
from shared_types import (
    BusinessCardExtraction,
    CandidateRegion,
    ExtractionMethod,
    FieldValue,
    OcrLine,
    OcrPage,
    Phone,
    QrFieldCheck,
    ReviewStatus,
    Script,
    Side,
)
from validation import EMAIL_CANDIDATE, PHONE_CANDIDATE, URL_CANDIDATE, parse_phone, validate_email_address, validate_url
from validation.postal import find_country
from validation.confidence import field_confidence

EXTRACTOR_VERSION = "1.1"
_HANDLE = re.compile(r"(?<![\w.])@([A-Za-z0-9_.]{2,30})\b")


def _host(url: str) -> str:
    return re.sub(r"^www\.", "", (url.split("/")[2] if "//" in url else url.split("/")[0])).lower()


def _apply_card_country(ex: BusinessCardExtraction) -> None:
    """A phone without an international prefix is normalised only with a country that is printed on
    the card itself (the business address). Language or city alone is never used."""
    if ex.address is None:
        return
    found = find_country(ex.address.original_text)
    if not found:
        return
    iso = found[1]  # find_country -> (printed text, ISO code)
    for i, p in enumerate(ex.phones):
        if p.e164 or p.original.strip().startswith(("+", "00")):
            continue
        parsed = parse_phone(p.original, iso)
        if parsed.is_valid:
            ex.phones[i] = p.model_copy(update={
                "e164": parsed.e164, "region": parsed.region, "region_inferred_from": "card_address", "is_valid": True,
                "review_status": ReviewStatus.needs_review,  # country came from context, confirm once
            })


_ROMAN_OCR = re.compile(r"(?<=[A-Za-zÀ-ÿ]\s)(lll|ll|Il|lI|IIl|IlI|lII)(?=\b)")


def _fix_roman_numerals(ex: BusinessCardExtraction) -> None:
    """'Hassan ll' -> 'Hassan II' in the address street (a frequent l/I confusion in street names).
    Only the structured ``street`` / ``normalized_text`` change; ``original_text`` stays as read."""
    a = ex.address
    if a is None or not a.street:
        return
    fixed = _ROMAN_OCR.sub(lambda m: m.group(0).replace("l", "I"), a.street)
    if fixed != a.street:
        ex.address = a.model_copy(update={"street": fixed, "normalized_text": _ROMAN_OCR.sub(lambda m: m.group(0).replace("l", "I"), a.normalized_text or a.original_text)})
        ex.warnings.append("ocr_correction:roman_numeral_in_street")


def _norm_name(s: str | None) -> str:
    return " ".join(sorted(normalize_search(s or "").replace("-", " ").split()))


def _qr_checks(ex: BusinessCardExtraction) -> None:
    """Compare QR contact data with OCR fields. Conflicts are reported and the OCR field is sent to
    review; the QR value is never copied into a field automatically."""
    single = {"fn": ("full_name", ex.full_name), "org": ("company", ex.company), "title": ("job_title", ex.job_title)}
    ocr_phone_tails = {re.sub(r"\D", "", p.e164 or digits_to_ascii(p.original))[-9:]: p for p in ex.phones}
    ocr_emails = {(e.value or "").lower() for e in ex.emails}
    for q in ex.qr_codes:
        data = dict(q.parsed)
        if q.kind == "mecard":  # MECARD uses N/ORG/TEL/EMAIL/URL
            data = {"fn": data.get("n", []), "org": data.get("org", []), "tel": data.get("tel", []), "email": data.get("email", []), "url": data.get("url", [])}
        if q.kind == "tel":
            data = {"tel": data.get("tel", [])}
        if q.kind == "email":
            data = {"email": data.get("email", [])}
        for key, (field, fv) in single.items():
            for v in data.get(key, [])[:1]:
                v = v.replace(";", " ").strip()
                if not v:
                    continue
                if fv.value is None:
                    ex.qr_checks.append(QrFieldCheck(field=field, qr_id=q.id, qr_value=v, status="qr_only"))
                elif _norm_name(v) == _norm_name(str(fv.original_value or fv.value)) or _norm_name(v) == _norm_name(str(fv.value)):
                    ex.qr_checks.append(QrFieldCheck(field=field, qr_id=q.id, qr_value=v, ocr_value=str(fv.value), status="match"))
                else:
                    ex.qr_checks.append(QrFieldCheck(field=field, qr_id=q.id, qr_value=v, ocr_value=str(fv.value), status="conflict"))
                    setattr(ex, field, fv.model_copy(update={"review_status": ReviewStatus.needs_review}))
                    ex.warnings.append(f"qr_conflict:{field}")
        for v in data.get("tel", []):
            tail = re.sub(r"\D", "", digits_to_ascii(v))[-9:]
            hit = ocr_phone_tails.get(tail)
            ex.qr_checks.append(QrFieldCheck(field="phones", qr_id=q.id, qr_value=v, ocr_value=hit.original if hit else None, status="match" if hit else "qr_only"))
            if not hit:
                ex.warnings.append("qr_value_not_on_card:phones")
        for v in data.get("email", []):
            ok = v.strip().lower() in ocr_emails
            ex.qr_checks.append(QrFieldCheck(field="emails", qr_id=q.id, qr_value=v, ocr_value=v if ok else None, status="match" if ok else "qr_only"))
            if not ok:
                ex.warnings.append("qr_value_not_on_card:emails")
        urls = data.get("url", [])
        for v in urls[:1]:
            if ex.website.value is None:
                ex.qr_checks.append(QrFieldCheck(field="website", qr_id=q.id, qr_value=v, status="qr_only"))
            elif _host(v) == _host(ex.website.value):
                ex.qr_checks.append(QrFieldCheck(field="website", qr_id=q.id, qr_value=v, ocr_value=ex.website.value, status="match"))
            else:
                ex.qr_checks.append(QrFieldCheck(field="website", qr_id=q.id, qr_value=v, ocr_value=ex.website.value, status="conflict"))
                ex.warnings.append("qr_conflict:website")


def _review_fields(ex: BusinessCardExtraction) -> list[str]:
    out: list[str] = []
    for name, value in ex:
        if isinstance(value, FieldValue) and value.value is not None and value.review_status == ReviewStatus.needs_review:
            out.append(name)
        elif isinstance(value, list):
            out += [f"{name}.{i}" for i, v in enumerate(value) if isinstance(v, (FieldValue, Phone)) and v.review_status == ReviewStatus.needs_review]
    if ex.address is not None and ex.address.review_status == ReviewStatus.needs_review:
        out.append("address")
    return out


def _title_hits(text: str) -> list[tuple[str, str | None, str | None]]:
    hits = match_titles(text)
    if not hits:
        extra = match_extra_title(text)
        if extra:
            hits = [(extra, EXTRA_TITLES.get(extra), None)]
    return hits


def _phone_type(line_text: str, match_start: int) -> tuple[str, str | None]:
    """Type only from an explicit label that precedes the number on the same line."""
    prefix = line_text[:match_start][-24:]
    for kind in ("whatsapp", "fax", "mobile", "phone"):
        terms = find_terms(prefix, PHONE_LABELS[kind])
        if terms:
            return kind, terms[-1]
    return "unknown", None


def _extract_contacts(lines: list[OcrLine], default_region: str | None, ex: BusinessCardExtraction) -> set[str]:
    used: set[str] = set()
    seen_emails: set[str] = set()
    seen_urls: set[str] = set()
    seen_phones: set[str] = set()
    email_spans_by_line: dict[str, list[tuple[int, int]]] = {}
    url_cands: list[tuple[bool, int, OcrLine, str, str, str | None]] = []
    for order, ln in enumerate(lines):
        text = digits_to_ascii(ln.text)
        email_spans: list[tuple[int, int]] = []
        for m in EMAIL_CANDIDATE.finditer(text):
            norm, err = validate_email_address(m.group(0))
            email_spans.append(m.span())
            key = norm or m.group(0)
            if key in seen_emails:
                continue
            seen_emails.add(key)
            ex.emails.append(
                make_field(norm or re.sub(r"\s+", "", m.group(0)), [ln], ExtractionMethod.rule, validated=err is None, original=m.group(0), normalized=norm, notes=None if err is None else f"invalid: {err}")
            )
            used.add(ln.id)
        email_spans_by_line[ln.id] = email_spans
        for m in URL_CANDIDATE.finditer(text):
            if any(a <= m.start() < b for a, b in email_spans):
                continue
            raw = m.group(0)
            norm, err = validate_url(raw)
            if norm:
                explicit = bool(re.match(r"(?i)(https?://|www\.)", raw))
                url_cands.append((not explicit, order, ln, raw, norm, err))
    # URLs written with www./http(s):// are stronger evidence than a bare domain, which may be a
    # fragment of a partly hidden e-mail or URL; assign the explicit ones first.
    url_cands.sort(key=lambda c: (c[0], c[1]))
    hosts = [_host(c[4]) for c in url_cands]
    for (bare, _, ln, raw, norm, err), host in zip(url_cands, hosts):
        if norm in seen_urls:
            continue
        seen_urls.add(norm)
        fragment_of = next((h for h in hosts if bare and h != host and h.endswith(host)), None)
        social = next((v for k, v in SOCIAL_DOMAINS.items() if host == k or host.endswith("." + k)), None)
        fv = make_field(norm, [ln], ExtractionMethod.rule, validated=err is None, original=raw, normalized=norm, notes=social)
        if fragment_of:
            ex.social_profiles.append(fv.model_copy(update={"notes": f"possible_fragment_of:{fragment_of}", "review_status": ReviewStatus.needs_review}))
            ex.warnings.append(f"possible_partial_text:{ln.id}")
        elif social == "linkedin" and ex.linkedin.value is None:
            ex.linkedin = fv
        elif social:
            ex.social_profiles.append(fv)
        elif ex.website.value is None:
            ex.website = fv if not bare else fv.model_copy(update={"notes": "bare_domain"})
        else:
            ex.social_profiles.append(fv.model_copy(update={"notes": "additional_url"}))
        used.add(ln.id)
    for ln in lines:
        text = digits_to_ascii(ln.text)
        email_spans = email_spans_by_line[ln.id]
        for m in _HANDLE.finditer(text):
            if any(a <= m.start() < b for a, b in email_spans):
                continue
            label = find_terms(text[: m.start()], ["twitter", "x", "instagram", "insta", "facebook", "tiktok", "linkedin"])
            ex.social_profiles.append(make_field("@" + m.group(1), [ln], ExtractionMethod.rule, original=m.group(0), notes=label[-1] if label else "handle_platform_unknown", force_review=not label))
            used.add(ln.id)
        for m in PHONE_CANDIDATE.finditer(text):
            if any(a <= m.start() < b for a, b in email_spans):
                continue
            raw = m.group(0).strip()
            parsed = parse_phone(raw, default_region)
            key = parsed.e164 or re.sub(r"\D", "", raw)
            if key in seen_phones:
                continue
            seen_phones.add(key)
            kind, evidence = _phone_type(text, m.start())
            conf = field_confidence([ln], "rule", parsed.is_valid)
            ex.phones.append(
                Phone(
                    type=kind,  # type: ignore[arg-type]
                    type_evidence=evidence,
                    original=ln.text[m.start() : m.end()] if len(ln.text) == len(text) else raw,
                    e164=parsed.e164,
                    region=parsed.region,
                    region_inferred_from=parsed.region_inferred_from,  # type: ignore[arg-type]
                    is_valid=parsed.is_valid,
                    confidence=conf,
                    source_region_ids=[ln.id],
                    review_status=ReviewStatus.unreviewed if parsed.is_valid and (conf or 0) >= 0.75 else ReviewStatus.needs_review,
                )
            )
            used.add(ln.id)
    # lines that are *only* contact data are consumed; mixed lines stay available
    return {l.id for l in lines if l.id in used and contact_coverage(l.text) > 0.6}


def _logo_candidate(pages: list[OcrPage], images: dict[Side, np.ndarray] | None) -> CandidateRegion | None:
    if not images:
        return None
    best: CandidateRegion | None = None
    for page in pages:
        img = images.get(page.side)
        if img is None:
            continue
        # 1–2 character "lines" inside a graphic are usually the OCR reading the logo itself
        text_boxes = [l.bbox for l in page.lines if len(re.sub(r"\W", "", l.text)) > 2]
        for i, (box, score) in enumerate(detect_color_patches(img, min_area_ratio=0.003, max_area_ratio=0.2)):
            overlap = any(not (b.x2 < box.x or b.x > box.x2 or b.y2 < box.y or b.y > box.y2) and (b.w * b.h) > 0.5 * box.w * box.h for b in text_boxes)
            if overlap:
                continue
            if best is None or score > (best.confidence or 0):
                best = CandidateRegion(id=f"{page.side.value[0]}-logo{i}", side=page.side, label="logo", bbox=box, confidence=round(score * 0.8, 3), method="heuristic:color_patch")
    return best


def _extract(
    pages: list[OcrPage],
    images: dict[Side, np.ndarray] | None = None,
    *,
    default_region: str | None = None,
) -> BusinessCardExtraction:
    ex = BusinessCardExtraction(extractor="rules", extractor_version=EXTRACTOR_VERSION, generated_at=datetime.now(timezone.utc))
    lines = all_lines(pages)
    ex.language_regions = summarize_languages(lines)
    ex.languages = sorted({r.language for r in ex.language_regions if r.language != "und"})
    for p in pages:
        ex.qr_codes.extend(p.qr_codes)
        if p.quality and p.quality.warnings:
            ex.warnings.extend(f"{p.side.value}:{w}" for w in p.quality.warnings)
    if not lines:
        ex.warnings.append("no_text_detected")
        return ex

    consumed = _extract_contacts(lines, default_region, ex)
    remaining = [l for l in lines if l.id not in consumed]

    # --- address: blocks with address evidence --------------------------------------
    best_block: list[OcrLine] | None = None
    best_score = 0
    for block in group_by_block(remaining).values():
        # only the address lines of the block (names/titles in the same block are left alone)
        addr_lines = [l for l in block if address_score(l.text) > 0]
        score = sum(address_score(l.text) for l in block)
        if addr_lines and score > best_score and score >= 2:
            best_block, best_score = addr_lines, score
    if best_block:
        ex.address = parse_address_block(best_block, "addr-0", role="business")
        consumed |= {l.id for l in best_block}
        remaining = [l for l in remaining if l.id not in consumed]

    # --- professional description ("Spécialiste des …"): kept verbatim, never a name/title ---
    desc_lines = [l for l in remaining if is_description(l.text)]
    if desc_lines:
        d = desc_lines[0]
        ex.professional_description = make_field(normalize_display(d.text), [d], ExtractionMethod.rule, original=d.text, notes="verbatim professional scope")
        remaining = [l for l in remaining if l.id not in {x.id for x in desc_lines}]

    # --- titles / industry / specialty --------------------------------------------------
    title_line: OcrLine | None = None
    title_hits: list[tuple[OcrLine, list[tuple[str, str | None, str | None]]]] = []
    for l in remaining:
        hits = _title_hits(l.text)
        # a job title is short; sentences that merely contain a title word are not titles
        if hits and len(l.text.split()) <= 8 and len(l.text) <= 60:
            title_hits.append((l, hits))

    # --- names ------------------------------------------------------------------------
    name_cands = [l for l in remaining if looks_like_name(l.text) and not _title_hits(strip_honorific(l.text)[0])]
    latin_names = [l for l in name_cands if detect_script(l.text) == Script.latin]
    arabic_names = [l for l in name_cands if detect_script(l.text) == Script.arabic]

    def rank(l: OcrLine) -> float:
        # larger text and higher position are typical of the person's name
        return l.bbox.h * 2 - (l.line_index or 0) * 0.5

    name_line = max(latin_names, key=rank) if latin_names else None
    if name_line is None and arabic_names:
        name_line = max(arabic_names, key=rank)
    if name_line is not None:
        core, honorific = strip_honorific(name_line.text)
        core = normalize_display(core)
        ex.full_name = make_field(core, [name_line], ExtractionMethod.layout, original=name_line.text, normalized=core, notes=f"honorific: {honorific}" if honorific else None)
        if detect_script(core) == Script.latin:
            first, last, rule = split_latin_name(core)
            if first and last:
                ex.first_name = make_field(first, [name_line], ExtractionMethod.layout, original=name_line.text, notes=f"split rule: {rule}", force_review=rule == "last_token")
                ex.last_name = make_field(last, [name_line], ExtractionMethod.layout, original=name_line.text, notes=f"split rule: {rule}", force_review=rule == "last_token")
    ar_line = next((l for l in sorted(arabic_names, key=rank, reverse=True) if l is not name_line), None)
    if ar_line is None and name_line is not None and detect_script(name_line.text) == Script.arabic:
        ar_line = name_line
    if ar_line is not None:
        core, honorific = strip_honorific(ar_line.text)
        ex.arabic_name = make_field(normalize_display(core), [ar_line], ExtractionMethod.layout, original=ar_line.text, notes=f"honorific: {honorific}" if honorific else None)

    used_ids = {x for f in (ex.full_name, ex.arabic_name) for x in f.source_region_ids}

    if title_hits:
        # prefer a title line next to the name line
        def title_rank(item: tuple[OcrLine, list]) -> float:
            l, hits = item
            dist = abs((l.line_index or 0) - (name_line.line_index or 0)) if name_line else 5
            return -dist + len(hits[0][0]) / 20
        title_line, hits = max(title_hits, key=title_rank)
        ex.job_title = make_field(normalize_display(title_line.text), [title_line], ExtractionMethod.rule, original=title_line.text, notes=f"matched: {hits[0][0]}")
        used_ids.add(title_line.id)
        industries = [h[1] for _, hs in title_hits for h in hs if h[1]]
        specialties = [(l, h) for l, hs in title_hits for h in hs if h[2]]
        if industries:
            ind = max(set(industries), key=industries.count)
            ev = [l for l, hs in title_hits if any(h[1] == ind for h in hs)]
            ex.industry = make_field(ind, ev, ExtractionMethod.rule, original=" | ".join(l.text for l in ev), notes="inferred from job-title keywords", force_review=True)
        if specialties:
            l, h = specialties[0]
            ex.specialty = make_field(h[2], [l], ExtractionMethod.rule, original=l.text, notes=f"inferred from '{h[0]}'")

    # --- company / department -------------------------------------------------------
    for l in remaining:
        if l.id in used_ids:
            continue
        if ex.department.value is None and has_term(l.text, DEPARTMENT_MARKERS) and not has_term(l.text, COMPANY_MARKERS):
            ex.department = make_field(normalize_display(l.text), [l], ExtractionMethod.rule, original=l.text)
            used_ids.add(l.id)
    company_line = next((l for l in remaining if l.id not in used_ids and has_term(l.text, COMPANY_MARKERS) and contact_coverage(l.text) < 0.3), None)
    method_note = "company marker"
    if company_line is None:
        domains = {e.value.split("@")[1].split(".")[0] for e in ex.emails if e.value and "@" in e.value}
        if ex.website.value:
            domains.add(ex.website.value.split("//")[-1].removeprefix("www.").split(".")[0])
        domains = {d for d in domains if d not in {"gmail", "yahoo", "hotmail", "outlook", "live", "icloud", "menara", "wanadoo", "orange", "free"}}
        for l in remaining:
            if l.id in used_ids:
                continue
            key = normalize_search(l.text).replace(" ", "").replace("-", "")
            if any(d and d.replace("-", "") in key for d in domains):
                company_line, method_note = l, "matches e-mail/website domain"
                break
    if company_line is not None:
        ex.company = make_field(normalize_display(company_line.text), [company_line], ExtractionMethod.rule, original=company_line.text, notes=method_note)
        used_ids.add(company_line.id)
        if ex.industry.value is None:
            for term, industry in (("clinique", "healthcare"), ("clinic", "healthcare"), ("hôpital", "healthcare"), ("hospital", "healthcare"), ("عيادة", "healthcare"), ("مستشفى", "healthcare"),
                                   ("université", "education"), ("university", "education"), ("école", "education"), ("school", "education"), ("جامعة", "education"), ("مدرسة", "education"),
                                   ("cabinet d'avocats", "legal"), ("law firm", "legal"), ("bank", "finance"), ("banque", "finance"), ("بنك", "finance")):
                if has_term(company_line.text, [term]):
                    ex.industry = make_field(industry, [company_line], ExtractionMethod.rule, original=company_line.text, notes=f"inferred from '{term}'", force_review=True)
                    break

    # --- explicit specialty printed on the card (overrides a title-keyword inference) ---
    for l in lines:
        found = find_specialty(l.text)
        if found:
            printed, canon = found
            ex.specialty = make_field(printed, [l], ExtractionMethod.rule, original=l.text, normalized=canon, notes="explicit specialty term printed on the card")
            break

    # --- "Dr" + explicit medical evidence -> job title "Médecin" (inferred, always reviewed) ---
    honorific = (ex.full_name.notes or "").split(":", 1)[1].strip() if (ex.full_name.notes or "").startswith("honorific:") else None
    medical = ex.specialty.value is not None and ex.specialty.notes == "explicit specialty term printed on the card"
    if ex.job_title.value is None and honorific and normalize_search(honorific) in MEDICAL_HONORIFICS and medical:
        name_lines = [l for l in lines if l.id in ex.full_name.source_region_ids]
        lang = "ar" if name_lines and detect_script(name_lines[0].text) == Script.arabic else ("en" if "en" in ex.languages and "fr" not in ex.languages else "fr")
        ex.job_title = make_field(INFERRED_DOCTOR_TITLE[lang], name_lines, ExtractionMethod.rule, original=None, notes=f"inferred: honorific '{honorific}' + printed medical specialty; not printed as a title", force_review=True)
        # not read from the card: confidence is capped so it never looks like a certain reading
        ex.job_title = ex.job_title.model_copy(update={"original_value": None, "confidence": min(ex.job_title.confidence or 0.5, 0.5)})
        if ex.industry.value is None:
            ex.industry = make_field("healthcare", name_lines, ExtractionMethod.rule, notes="inferred from medical specialty", force_review=True)
            ex.industry = ex.industry.model_copy(update={"confidence": min(ex.industry.confidence or 0.5, 0.5)})

    # --- qualifications / certifications / memberships -----------------------------
    for l in lines:
        for q in find_patterns(l.text, QUALIFICATION_PATTERNS):
            ex.qualifications.append(make_field(q, [l], ExtractionMethod.rule, original=l.text))
        for c in find_patterns(l.text, CERTIFICATION_PATTERNS):
            ex.certifications.append(make_field(c, [l], ExtractionMethod.rule, original=l.text))
        for m in find_patterns(l.text, MEMBERSHIP_PATTERNS):
            ex.memberships.append(make_field(m, [l], ExtractionMethod.rule, original=l.text))
    if ex.full_name.notes and ex.full_name.notes.startswith("honorific:"):
        h = ex.full_name.notes.split(":", 1)[1].strip()
        if normalize_search(h).rstrip(".") in {"dr", "pr", "prof", "docteur", "professeur", "الدكتور", "الدكتورة", "د"}:
            ex.qualifications.append(make_field(h, [l for l in lines if l.id in ex.full_name.source_region_ids], ExtractionMethod.rule, notes="academic/medical title printed before the name"))

    ex.logo = _logo_candidate(pages, images)
    _apply_card_country(ex)
    _fix_roman_numerals(ex)
    _qr_checks(ex)
    if not ex.full_name.value:
        ex.warnings.append("name_not_found")
    for l in lines:
        for alt in l.alternatives:
            if "digits_possibly_dropped" in alt.get("flags", []):
                ex.warnings.append(f"digits_possibly_dropped:{l.id}")
    ex.review_fields = _review_fields(ex)
    return ex


def extract_business_card(
    pages: list[OcrPage],
    images: dict[Side, np.ndarray] | None = None,
    *,
    default_region: str | None = None,
) -> tuple[BusinessCardExtraction, list[CandidateRegion]]:
    """Returns the extraction and candidate regions (logo, QR codes)."""
    ex = _extract(pages, images, default_region=default_region)
    regions: list[CandidateRegion] = []
    if ex.logo is not None:
        regions.append(ex.logo)
    for q in ex.qr_codes:
        if q.bbox is not None:
            regions.append(CandidateRegion(id=q.id, side=q.side, label="qr", bbox=q.bbox, confidence=None, method="opencv:qr"))
    return ex, regions


def dedupe_keys(ex: BusinessCardExtraction | dict) -> list[str]:
    data = ex if isinstance(ex, dict) else ex.model_dump(mode="json")
    keys: set[str] = set()
    for e in data.get("emails") or []:
        if e.get("value"):
            keys.add("email:" + str(e["value"]).lower())
    for p in data.get("phones") or []:
        digits = p.get("e164") or re.sub(r"\D", "", digits_to_ascii(p.get("original") or ""))
        if digits and len(re.sub(r"\D", "", digits)) >= 8:
            keys.add("phone:" + re.sub(r"\D", "", digits)[-9:])  # last 9 digits: robust to +212 / 0 prefixes
    for f in ("full_name", "arabic_name"):
        v = (data.get(f) or {}).get("value")
        if v:
            keys.add("name:" + normalize_search(str(v)))
    return sorted(keys)


__all__ = ["extract_business_card", "dedupe_keys", "EXTRACTOR_VERSION"]
