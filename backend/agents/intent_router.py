"""Structured semantic routing with a deterministic, auditable fallback."""
from __future__ import annotations

import json
import re
from typing import Callable

from pydantic import ValidationError

from agents.contracts import FULL_DECISION_CONTEXT, IntentDecision


SPECIALIST_ORDER = ("guardian", "portfolio", "tax", "cashflow")
DOMAIN_PATTERNS = {
    "guardian": (
        r"\b(?:fraud|scam|suspicious|unusual|anomal(?:y|ies|ous)|not mine|unauthori[sz]ed|do not recognize)\b",
        r"\b(?:transaction|charge) (?:looks? wrong|I do not recognize)\b",
    ),
    "portfolio": (
        r"\b(?:portfolio|holding|allocation|diversif|concentrat|net worth|asset mix|performance|volatility|drawdown|market prices?|valuation)\w*\b",
        r"\b(?:too much|exposed) (?:in|to)\b",
    ),
    "tax": (
        r"\b(?:tax|capital gain|ltcg|stcg|deduction|80c|taxable|filing)\w*\b",
        r"\b(?:sell|sale|redeem)\w*\b.*\b(?:impact|cost|owe)\w*\b",
    ),
    "cashflow": (
        r"\b(?:cash ?flow|spend|expense|income|budget|surplus|afford|emergency fund|liquidit)\w*\b",
        r"\b(?:money left|monthly burn|runway|cash needs?)\b",
    ),
}
ACTION_RE = re.compile(r"\b(?:should I|what should I|recommend|buy|sell|invest|rebalance|allocate|best investment|second opinion|compare investments|compare options)\b", re.I)
EXECUTION_RE = re.compile(
    r"\b(?:execute|place|submit|make) (?:a |the )?(?:(?:buy|sell) )?(?:trade|order|purchase|sale)\b"
    r"|^\s*(?:(?:please|can you|could you|would you)\s+)*(?:buy|sell|purchase)\b",
    re.I,
)
GUARANTEE_RE = re.compile(r"\b(?:guaranteed?|risk[- ]free) (?:return|profit|gain)s?\b", re.I)
UNDERSPECIFIED_RE = re.compile(
    r"\b(?:is (?:that|this|it)|what about|something about|situation with)\b", re.I
)


class StructuredIntentRouter:
    def __init__(self, semantic_classifier: Callable[[str], str | dict] | None = None):
        self.semantic_classifier = semantic_classifier

    def route(self, message: str) -> IntentDecision:
        if self.semantic_classifier is not None:
            try:
                raw = self.semantic_classifier(message)
                payload = json.loads(raw) if isinstance(raw, str) else raw
                decision = IntentDecision.model_validate({**payload, "route_source": "semantic_model"})
                return self._enforce_safety(message, decision)
            except (ValueError, TypeError, ValidationError, json.JSONDecodeError):
                pass
        return self._fallback(message)

    def _fallback(self, message: str) -> IntentDecision:
        text = " ".join(message.strip().split())
        lowered = text.lower()
        specialists = [
            name for name in SPECIALIST_ORDER
            if any(re.search(pattern, lowered, re.I) for pattern in DOMAIN_PATTERNS[name])
        ]
        unsupported = bool(EXECUTION_RE.search(text) or GUARANTEE_RE.search(text))
        action = bool(ACTION_RE.search(text))
        clarification = not specialists and (
            len(text.split()) < 3 or bool(UNDERSPECIFIED_RE.search(text))
        )
        educational = bool(re.match(r"^(?:explain|what is|what does|teach me|define)\b", text, re.I)) and not re.search(r"\b(?:my|mine|I|me)\b", text)

        if unsupported:
            primary = "unsupported"
        elif clarification:
            primary = "clarification"
        elif action:
            primary = "recommendation_like"
            specialists = list(SPECIALIST_ORDER)
        elif educational:
            primary = "informational_education"
            specialists = []
        elif len(specialists) > 1:
            primary = "cross_domain_analysis"
        elif specialists:
            primary = "user_specific_analysis"
        else:
            primary = "informational_education"

        contexts = set()
        mapping = {
            "guardian": {"guardian", "transactions"},
            "portfolio": {"holdings", "market"},
            "tax": {"transactions"},
            "cashflow": {"cashflow"},
        }
        for specialist in specialists:
            contexts.update(mapping[specialist])
        if action:
            contexts.update(FULL_DECISION_CONTEXT)
        return IntentDecision(
            primary_intent=primary,
            secondary_intents=specialists,
            required_specialists=specialists,
            required_private_contexts=contexts,
            requires_public_knowledge=primary in {"informational_education", "cross_domain_analysis", "recommendation_like"} or "tax" in specialists or bool(re.search(r"\b(?:current|recent|latest)\b.*\b(?:market|economic)\b|\b(?:market|economic)\b.*\b(?:conditions|outlook)\b", lowered)),
            risk_level="high" if action or unsupported else "medium" if specialists else "low",
            clarification_required=clarification,
            confidence=0.92 if unsupported else 0.82 if specialists else 0.65,
            route_source="deterministic_fallback",
        )

    @staticmethod
    def _enforce_safety(message: str, decision: IntentDecision) -> IntentDecision:
        if ACTION_RE.search(message):
            decision.primary_intent = "recommendation_like"
            decision.risk_level = "high"
            decision.required_specialists = list(SPECIALIST_ORDER)
            decision.required_private_contexts.update(FULL_DECISION_CONTEXT)
        if EXECUTION_RE.search(message) or GUARANTEE_RE.search(message):
            decision.primary_intent = "unsupported"
            decision.risk_level = "high"
        return decision
