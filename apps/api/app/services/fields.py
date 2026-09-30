"""Manual correction engine for ``documents.data``.

* ``set``    – replace a value; FieldValue targets become ``extraction_method=manual``,
               ``review_status=corrected``, ``confidence=None`` (no OCR estimate for human input).
               The OCR evidence (``original_value``, ``source_region_ids``) is kept.
* ``verify`` – mark a FieldValue / Address / Phone as verified without changing it.
* ``append`` / ``remove`` – list fields (emails, phones, addresses, qualifications …).

Every change is validated against the product's Pydantic schema before it is committed."""

from __future__ import annotations

import copy
import uuid
from typing import Any

from pydantic import BaseModel, ValidationError

from app.errors import ApiError
from validation import parse_phone, validate_email_address, validate_url

READ_ONLY_TOP = {"schema_version", "extractor", "extractor_version", "generated_at", "language_regions", "warnings", "logo", "qr_checks", "review_fields"}
READ_ONLY_LEAVES = {"raw", "kind", "parsed", "url_is_safe", "bbox", "source_region_ids", "extraction_method", "original_value", "id"}

FIELD_KEYS = {"value", "extraction_method", "review_status"}


def _is_field(obj: Any) -> bool:
    return isinstance(obj, dict) and FIELD_KEYS <= set(obj)


def _manual_field(value: Any, prev: dict | None = None) -> dict:
    prev = prev or {}
    return {
        "value": value,
        "original_value": prev.get("original_value"),
        "normalized_value": None,
        "confidence": None,
        "source_region_ids": prev.get("source_region_ids", []),
        "extraction_method": "manual",
        "review_status": "corrected",
        "notes": prev.get("notes"),
    }


def _validate_scalar(path: str, value: Any) -> Any:
    leaf = path.split(".")[0]
    if value in (None, ""):
        return None
    if leaf == "emails":
        norm, err = validate_email_address(str(value))
        if err:
            raise ApiError(422, "invalid_email", "The e-mail address is not valid.", {"path": path})
        return norm
    if leaf in ("website", "linkedin") or (leaf == "social_profiles" and str(value).startswith(("http", "www"))):
        norm, err = validate_url(str(value))
        if err:
            raise ApiError(422, "invalid_url", "The URL is not valid (only http/https).", {"path": path})
        return norm
    return value


def _navigate(data: dict, path: str) -> tuple[Any, str | int]:
    parts = path.split(".")
    if parts[0] in READ_ONLY_TOP:
        raise ApiError(422, "read_only_field", f"'{parts[0]}' cannot be edited.", {"path": path})
    if parts[-1] in READ_ONLY_LEAVES:
        raise ApiError(422, "read_only_field", f"'{parts[-1]}' cannot be edited.", {"path": path})
    cur: Any = data
    for p in parts[:-1]:
        cur = _step(cur, p, path)
    last: str | int = int(parts[-1]) if parts[-1].isdigit() else parts[-1]
    if isinstance(cur, list) and not isinstance(last, int):
        raise ApiError(422, "invalid_path", "Invalid field path.", {"path": path})
    if isinstance(cur, dict) and isinstance(last, int):
        raise ApiError(422, "invalid_path", "Invalid field path.", {"path": path})
    if cur is None:
        raise ApiError(422, "invalid_path", "Invalid field path.", {"path": path})
    return cur, last


def _step(cur: Any, p: str, path: str) -> Any:
    try:
        if isinstance(cur, list):
            return cur[int(p)]
        if isinstance(cur, dict) and p in cur:
            return cur[p]
    except (ValueError, IndexError):
        pass
    raise ApiError(422, "invalid_path", "Invalid field path.", {"path": path})


def _new_list_item(list_name: str, value: Any, default_region: str | None) -> Any:
    if list_name == "phones":
        raw = value.get("original") if isinstance(value, dict) else str(value)
        if not raw:
            raise ApiError(422, "invalid_phone", "A phone number is required.")
        parsed = parse_phone(raw, default_region)
        kind = value.get("type", "unknown") if isinstance(value, dict) else "unknown"
        return {
            "type": kind, "type_evidence": "manual", "original": raw, "e164": parsed.e164, "region": parsed.region,
            "region_inferred_from": parsed.region_inferred_from, "is_valid": parsed.is_valid, "confidence": None,
            "source_region_ids": [], "review_status": "corrected",
        }
    if list_name == "addresses":
        if not isinstance(value, dict) or not value.get("original_text"):
            raise ApiError(422, "invalid_address", "original_text is required.")
        return {**value, "id": f"addr-m{uuid.uuid4().hex[:6]}", "extraction_method": "manual", "review_status": "corrected", "source_region_ids": []}
    return _manual_field(_validate_scalar(list_name, value))


def apply_changes(data: dict, changes: list, schema: type[BaseModel], *, default_region: str | None = None) -> tuple[dict, list[dict]]:
    """Returns (new_data, events). Raises ApiError on invalid input."""
    new = copy.deepcopy(data)
    events: list[dict] = []
    for ch in changes:
        parent, key = _navigate(new, ch.path)
        old = copy.deepcopy(parent[key]) if (isinstance(parent, dict) and key in parent) or (isinstance(parent, list) and isinstance(key, int) and key < len(parent)) else None
        if ch.op == "set":
            if isinstance(parent, dict) and key not in parent:
                raise ApiError(422, "invalid_path", "Invalid field path.", {"path": ch.path})
            target = parent[key]
            if _is_field(target):
                parent[key] = _manual_field(_validate_scalar(ch.path, ch.value), target)
            elif isinstance(target, (dict, list)) and not isinstance(ch.value, type(target)):
                raise ApiError(422, "invalid_value", "Value has the wrong type.", {"path": ch.path})
            else:
                value = ch.value
                if key == "e164" and value:
                    p = parse_phone(str(value))
                    if not p.is_valid:
                        raise ApiError(422, "invalid_phone", "E.164 number is not valid.", {"path": ch.path})
                    value = p.e164
                parent[key] = value
                if isinstance(parent, dict) and "review_status" in parent and key != "review_status":
                    parent["review_status"] = "corrected"
                if isinstance(parent, dict) and "extraction_method" in parent and key != "role":
                    parent["extraction_method"] = "manual"
            new_value = parent[key]
            action = "field_set"
        elif ch.op == "verify":
            target = parent[key]
            if not isinstance(target, dict) or "review_status" not in target:
                raise ApiError(422, "invalid_path", "Only fields, addresses and phones can be verified.", {"path": ch.path})
            target["review_status"] = "verified"
            new_value = {"review_status": "verified"}
            action = "field_verify"
        elif ch.op == "append":
            target = parent[key]
            if not isinstance(target, list):
                raise ApiError(422, "invalid_path", "Append requires a list field.", {"path": ch.path})
            item = _new_list_item(str(key), ch.value, default_region)
            target.append(item)
            new_value = item
            action = "field_append"
        else:  # remove
            if not isinstance(parent, list) or not isinstance(key, int) or key >= len(parent):
                raise ApiError(422, "invalid_path", "Remove requires a list item path.", {"path": ch.path})
            parent.pop(key)
            new_value = None
            action = "field_remove"
        events.append({"action": action, "path": ch.path, "old_value": old, "new_value": new_value})

    _refresh_review_fields(new)
    try:
        validated = schema.model_validate(new)
    except ValidationError as exc:
        raise ApiError(422, "schema_validation_failed", "The corrected document does not match the schema.", {"errors": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()][:20]}) from exc
    return validated.model_dump(mode="json"), events


def _refresh_review_fields(data: dict) -> None:
    """Recompute the list of paths still needing review after edits."""
    if "review_fields" not in data:
        return
    out: list[str] = []
    for k, val in data.items():
        if isinstance(val, dict) and val.get("review_status") == "needs_review" and (val.get("value") is not None or "original_text" in val):
            out.append(k)
        elif isinstance(val, list):
            out += [f"{k}.{i}" for i, x in enumerate(val) if isinstance(x, dict) and x.get("review_status") == "needs_review"]
    data["review_fields"] = out
