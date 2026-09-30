"""Per-region recognizer selection.

Each detected line crop may be recognized by several script-specific models. We keep the
hypothesis that is *script-consistent* and best scored. Rationale (verified on PaddleOCR 3.3.3):
the Latin model emits blanks/garbage for Arabic crops, while the Arabic model also reads
Latin characters and digits – so "highest score wins" alone would be wrong."""

from __future__ import annotations

import re

from language_detection import script_counts

_DIGIT_RUN = re.compile(r"\d{2,}")


def choose_hypothesis(hyps: dict[str, tuple[str, float]]) -> tuple[str, str, float, list[str]]:
    """``hyps``: model_key -> (text, score). Returns (model_key, text, score, flags)."""
    flags: list[str] = []
    cleaned = {k: (t.strip(), float(s)) for k, (t, s) in hyps.items()}
    arabic = cleaned.get("arabic")
    latin_keys = [k for k in cleaned if k != "arabic"]
    best_latin = max((cleaned[k] + (k,) for k in latin_keys), key=lambda x: x[1], default=None)

    def arabic_share(text: str) -> float:
        c = script_counts(text)
        letters = c["arabic"] + c["latin"] + c["other_letter"]
        return c["arabic"] / letters if letters else 0.0

    if arabic and arabic[0] and arabic_share(arabic[0]) >= 0.3:
        choice = ("arabic", arabic[0], arabic[1])
        if best_latin and best_latin[0]:
            lat_text = best_latin[0]
            if arabic_share(lat_text) == 0 and best_latin[1] > arabic[1] + 0.15 and script_counts(lat_text)["latin"] >= 3:
                choice = (best_latin[2], lat_text, best_latin[1])
            else:
                missing = [d for d in _DIGIT_RUN.findall(lat_text) if d not in arabic[0]]
                if missing:
                    flags.append("digits_possibly_dropped")
        return (*choice, flags)

    if best_latin and best_latin[0]:
        if arabic and arabic[0] and arabic[1] > best_latin[1] + 0.05 and arabic_share(arabic[0]) == 0:
            # both read Latin text; Arabic model's Latin reading scored clearly higher
            return ("arabic", arabic[0], arabic[1], flags)
        return (best_latin[2], best_latin[0], best_latin[1], flags)

    if arabic and arabic[0]:
        return ("arabic", arabic[0], arabic[1], flags)
    # nothing readable – keep the best empty/whitespace score so the region is still reported
    key = max(cleaned, key=lambda k: cleaned[k][1])
    return (key, cleaned[key][0], cleaned[key][1], ["unreadable"])
