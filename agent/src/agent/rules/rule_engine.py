"""Deterministic rule engine: keyword scoring, negation detection, routing decision.

Scoring formula: score = (matched_unique_keywords / total_unique_keywords) * confidence_base
  - All keywords are normalized (lowercase, diacritics stripped) before matching.
  - required_keywords act as an AND gate: every entry must appear or the rule scores 0.
  - If a negation phrase is detected anywhere in the message, the score is multiplied by 0.5.

Decision thresholds:
  - escalate_human: score >= 0.30  (evaluated first — human safety over auto-resolve)
  - resolved:       score >= 0.40
  - escalate_llm:   fallback when no rule meets its threshold
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

_CATALOG_PATH = Path(__file__).parent / "faq_catalog.json"

DecisionType = Literal["resolved", "escalate_human", "escalate_llm"]

_RESOLVE_THRESHOLD: float = 0.40
_HUMAN_THRESHOLD: float = 0.30

# Negation phrases that, when found anywhere in the message, halve the score.
_NEGATION_PHRASES: tuple[str, ...] = (
    "no quiero",
    "no deseo",
    "no necesito",
    "no me interesa",
    "no busco",
)


@dataclass(frozen=True)
class MatchResult:
    decision: DecisionType
    confidence: float
    rule_id: str | None
    response: str | None
    escalation_phone: str | None


def _normalize(text: str) -> str:
    """Lowercase and strip diacritics so 'contraseña'=='contrasena' after matching."""
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def _load_catalog() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    return data


def _score_rule(rule: dict[str, Any], normalized_message: str) -> float:
    """Return a score in [0, confidence_base]; 0 means the rule does not match."""
    keywords: list[str] = rule.get("keywords", [])
    required: list[str] = rule.get("required_keywords", [])
    confidence_base: float = float(rule.get("confidence_base", 1.0))

    # AND gate: every required keyword must be present in the message.
    if any(_normalize(kw) not in normalized_message for kw in required):
        return 0.0

    # Deduplicate after normalisation to avoid inflating the denominator.
    norm_kws: list[str] = list(dict.fromkeys(_normalize(kw) for kw in keywords))
    if not norm_kws:
        return 0.0

    matched = sum(1 for kw in norm_kws if kw in normalized_message)
    if matched == 0:
        return 0.0

    return (matched / len(norm_kws)) * confidence_base


def match(message: str) -> MatchResult:
    """Score all catalog rules and return the highest-confidence routing decision.

    Human-escalation rules are evaluated first and take priority over auto-resolve.
    """
    catalog = _load_catalog()
    normalized = _normalize(message)

    has_negation = any(phrase in normalized for phrase in _NEGATION_PHRASES)

    best_human: tuple[float, dict[str, Any]] | None = None
    best_resolve: tuple[float, dict[str, Any]] | None = None

    for rule in catalog:
        score = _score_rule(rule, normalized)
        if score == 0.0:
            continue
        if has_negation:
            score *= 0.5

        if rule.get("requires_human"):
            if best_human is None or score > best_human[0]:
                best_human = (score, rule)
        else:
            if best_resolve is None or score > best_resolve[0]:
                best_resolve = (score, rule)

    if best_human is not None and best_human[0] >= _HUMAN_THRESHOLD:
        s, rule = best_human
        return MatchResult(
            decision="escalate_human",
            confidence=round(s, 4),
            rule_id=str(rule["id"]),
            response=str(rule.get("response", "")),
            escalation_phone=str(rule.get("escalation_phone") or "") or None,
        )

    if best_resolve is not None and best_resolve[0] >= _RESOLVE_THRESHOLD:
        s, rule = best_resolve
        return MatchResult(
            decision="resolved",
            confidence=round(s, 4),
            rule_id=str(rule["id"]),
            response=str(rule.get("response", "")),
            escalation_phone=None,
        )

    return MatchResult(
        decision="escalate_llm",
        confidence=0.0,
        rule_id=None,
        response=None,
        escalation_phone=None,
    )
