"""Fail-closed validation for material numbers in conversational output."""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any


MATERIAL_NUMBER_RE = re.compile(
    r"(?i)(?:(?:₹|rs\.?|inr)\s*([-+]?\d[\d,]*(?:\.\d+)?)|([-+]?\d[\d,]*(?:\.\d+)?)\s*(%|percent\b))"
)
ANY_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?")
SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|\n|$)")


def _normal(value: str) -> str | None:
    try:
        parsed = Decimal(value.replace(",", ""))
        if parsed == parsed.to_integral_value():
            return str(int(parsed))
        return format(parsed, "f").rstrip("0").rstrip(".")
    except (InvalidOperation, ValueError):
        return None


def validate_material_numbers(response: str, evidence: Any) -> tuple[str, list[str]]:
    """Remove sentences containing currency/percentage values absent from evidence.

    General counts and dates are intentionally excluded; this layer protects the
    financial values most likely to cause harm while specialist claim validation
    remains responsible for structured calculations.
    """
    evidence_text = json.dumps(evidence, default=str, sort_keys=True)
    allowed = {_normal(match.group(0)) for match in ANY_NUMBER_RE.finditer(evidence_text)}
    allowed.discard(None)
    unsupported: list[str] = []
    safe_parts: list[str] = []
    for sentence in SENTENCE_RE.findall(response):
        claims = []
        for match in MATERIAL_NUMBER_RE.finditer(sentence):
            raw = match.group(1) or match.group(2)
            normalized = _normal(raw)
            if normalized not in allowed:
                claims.append(match.group(0).strip())
        if claims:
            unsupported.extend(claims)
        else:
            safe_parts.append(sentence)
    safe = "".join(safe_parts).strip()
    if unsupported and not safe:
        safe = "I could not verify the material financial figures in the generated response against the available evidence."
    return safe, list(dict.fromkeys(unsupported))
