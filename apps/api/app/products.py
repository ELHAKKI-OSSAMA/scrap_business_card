"""Business-card product definition: schema, extraction, summary, search fields and exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from pydantic import BaseModel

from extraction import (
    BUSINESS_CSV_COLUMNS,
    business_row,
    extract_business_card,
)
from shared_types import BusinessCardExtraction, CandidateRegion, OcrPage, Side


def _v(d: dict | None, key: str) -> Any:
    f = (d or {}).get(key)
    return f.get("value") if isinstance(f, dict) else None


def _card_summary(data: dict | None) -> dict:
    d = data or {}
    phones = d.get("phones") or []
    emails = d.get("emails") or []
    return {
        "full_name": _v(d, "full_name") or _v(d, "arabic_name"),
        "arabic_name": _v(d, "arabic_name"),
        "job_title": _v(d, "job_title"),
        "company": _v(d, "company"),
        "email": emails[0].get("value") if emails else None,
        "phone": (phones[0].get("e164") or phones[0].get("original")) if phones else None,
    }


def _card_search_fields(data: dict) -> list[str]:
    out = [str(_v(data, k) or "") for k in ("full_name", "arabic_name", "job_title", "company", "department", "industry", "specialty", "website")]
    out += [str(e.get("value") or "") for e in data.get("emails") or []]
    out += [str(p.get("original") or "") + " " + str(p.get("e164") or "") for p in data.get("phones") or []]
    if data.get("address"):
        out.append(data["address"].get("original_text") or "")
    return out


ExtractFn = Callable[[list[OcrPage], dict[Side, np.ndarray], dict], tuple[BaseModel, list[CandidateRegion]]]


@dataclass(frozen=True)
class ProductSpec:
    key: str
    route: str
    schema: type[BaseModel]
    extract: ExtractFn
    summary: Callable[[dict | None], dict]
    search_fields: Callable[[dict], list[str]]
    csv_columns: list[str]
    csv_row: Callable[[dict], dict]
    export_formats: tuple[str, ...]


BUSINESS_CARD = ProductSpec(
    key="business_card",
    route="business-cards",
    schema=BusinessCardExtraction,
    extract=lambda pages, images, opts: extract_business_card(pages, images, default_region=opts.get("default_phone_region")),
    summary=_card_summary,
    search_fields=_card_search_fields,
    csv_columns=BUSINESS_CSV_COLUMNS,
    csv_row=business_row,
    export_formats=("json", "csv", "vcf"),
)

PRODUCTS = {BUSINESS_CARD.key: BUSINESS_CARD}
