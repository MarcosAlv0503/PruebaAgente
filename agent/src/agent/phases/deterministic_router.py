"""Phase 1b — deterministic_router: rule-based resolution before any LLM call.

Decision outcomes:
  resolved        → sets final_response + log_ref; pipeline stops here (cost: zero)
  escalate_human  → sets final_response with phone; pipeline stops here (cost: zero)
  escalate_llm    → state unchanged; classify phase runs next (cost: haiku)
"""
from __future__ import annotations

from typing import Any

from agent._logging import get_logger
from agent.rules import rule_engine
from agent.tools.write_log import write_log

_LOGGER = get_logger("phase.deterministic_router")
_PHASE = "deterministic"


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Match incident message against FAQ catalog and route accordingly.

    If a conversation is already in progress (conversation_history is non-empty),
    the LLM handles the follow-up using full context — no deterministic routing.
    """
    execution_id: str = str(state["execution_id"])
    message: str = str(state.get("incident_message", ""))
    conversation_history: list[dict[str, str]] = list(state.get("conversation_history") or [])

    if conversation_history:
        _LOGGER.info(
            "[phase.deterministic_router] execution=%s has_history=true — deferring to LLM",
            execution_id,
        )
        state["deterministic_decision"] = "escalate_llm"
        state["deterministic_confidence"] = 0.0
        state["escalation_phone"] = None
        return state

    result = rule_engine.match(message)

    state["deterministic_decision"] = result.decision
    state["deterministic_confidence"] = result.confidence

    _LOGGER.info(
        "[phase.deterministic_router] execution=%s decision=%s confidence=%.4f rule=%s",
        execution_id,
        result.decision,
        result.confidence,
        result.rule_id,
    )

    if result.decision == "resolved":
        response = str(result.response or "")
        category = str(state.get("initial_category") or "faq")
        severity = str(state.get("initial_severity") or "low")

        state["classification"] = {
            "type": category,
            "severity": severity,
            "confidence": result.confidence,
        }
        state["final_response"] = response
        state["needs_heavy"] = False
        state["escalation_phone"] = None
        state["log_ref"] = write_log(
            _PHASE,
            incident_id=execution_id,
            execution_id=execution_id,
            reporter=str(state.get("reporter", "unknown")),
            channel=str(state.get("channel", "web")),
            incident_type=category,
            severity=severity,
            confidence=result.confidence,
            auto_resolved=True,
            message=message,
            response=response,
            kb_refs=[],
        )
        _LOGGER.info(
            "[phase.deterministic_router] execution=%s resolved rule=%s",
            execution_id,
            result.rule_id,
        )

    elif result.decision == "escalate_human":
        phone = str(result.escalation_phone or "")
        base_response = str(result.response or "")
        response = f"{base_response}\n\nEquipo de atención al cliente: {phone}".strip()

        state["classification"] = {
            "type": str(state.get("initial_category") or "complaint"),
            "severity": "high",
            "confidence": result.confidence,
        }
        state["final_response"] = response
        state["needs_heavy"] = False
        state["escalation_phone"] = phone
        state["log_ref"] = write_log(
            _PHASE,
            incident_id=execution_id,
            execution_id=execution_id,
            reporter=str(state.get("reporter", "unknown")),
            channel=str(state.get("channel", "web")),
            incident_type=str(state["classification"]["type"]),
            severity="high",
            confidence=result.confidence,
            auto_resolved=False,
            message=message,
            response=response,
            kb_refs=[],
        )
        _LOGGER.info(
            "[phase.deterministic_router] execution=%s escalate_human phone=%s rule=%s",
            execution_id,
            phone,
            result.rule_id,
        )

    else:
        # escalate_llm: leave state untouched — classify phase picks up from here
        state["escalation_phone"] = None

    return state
