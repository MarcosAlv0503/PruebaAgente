"""LangGraph driver: orchestrates the three phases for the ecommerce support agent.

Pipeline:
  1. phase_deterministic (intake.py)  — validate, dedup, keywords
  2. phase_light_llm    (classify.py) — classify with haiku + KB search
  3. phase_heavy_llm    (escalate.py) — escalate with sonnet (conditional)
"""
from __future__ import annotations

from typing import Any, TypedDict

import agent.phases.deterministic_router as deterministic_router_phase
import agent.phases.escalate as escalate_phase
import agent.phases.classify as classify_phase
import agent.phases.intake as intake_phase
from agent._logging import get_logger

_LOGGER = get_logger("graph")


class State(TypedDict):
    # --- core: inherited from template, do not rename or remove ---
    execution_id: str
    customer_id: str
    input: dict[str, Any]
    summary: str | None
    light_output: dict[str, Any] | None
    heavy_output: dict[str, Any] | None

    # --- phase 1: intake (deterministic) ---
    incident_message: str
    reporter: str
    channel: str
    reported_at: str
    is_duplicate: bool
    customer_context: dict[str, Any] | None
    extracted_keywords: list[str]
    initial_category: str | None
    initial_severity: str | None

    # --- phase 1b: deterministic router ---
    deterministic_decision: str | None  # "resolved" | "escalate_human" | "escalate_llm"
    deterministic_confidence: float
    escalation_phone: str | None

    # --- phase 2: classification (light_llm) ---
    classification: dict[str, Any] | None  # type, severity, confidence
    kb_results: list[dict[str, Any]]
    proposed_response: str | None
    needs_heavy: bool

    # --- phase 3: escalation (heavy_llm, conditional) ---
    ticket: dict[str, Any] | None
    escalation_reason: str | None

    # --- multi-turn conversation ---
    thread_id: str | None
    conversation_history: list[dict[str, str]]

    # --- final output ---
    final_response: str | None
    log_ref: str | None
    ticket_ref: str | None


def build_summary(state: State) -> str:
    """Build a compact summary string for executions.output and audit trail."""
    classification = state.get("classification") or {}
    deterministic = state.get("deterministic_decision")
    parts: list[str] = [
        f"type={classification.get('type', 'unknown')}",
        f"severity={classification.get('severity', 'unknown')}",
        f"confidence={classification.get('confidence', 0.0):.2f}",
        f"auto_resolved={not state.get('needs_heavy', False)}",
    ]
    if deterministic:
        parts.append(f"deterministic={deterministic}")
    if state.get("log_ref"):
        parts.append(f"log={state['log_ref']}")
    if state.get("ticket_ref"):
        parts.append(f"ticket={state['ticket_ref']}")
    return " | ".join(parts)


def run(state: State) -> State:
    """Run the pipeline.

    Pipeline:
      1. intake              — validate, dedup, keywords (always runs)
      2. deterministic_router — rule-based resolution (always runs unless duplicate)
         → resolved        : final_response set, pipeline stops (zero LLM cost)
         → escalate_human  : final_response + phone set, pipeline stops (zero LLM cost)
         → escalate_llm    : continue to LLM phases
      3. classify_llm        — haiku classification + KB search (only on escalate_llm)
      4. escalate_llm        — sonnet deep analysis + ticket (only when classify requests it)
    """
    state = intake_phase.run(state)  # type: ignore[arg-type]

    if state["is_duplicate"]:
        _LOGGER.info("[graph] execution=%s is_duplicate=true — skipping all phases", state["execution_id"])
        state["final_response"] = "Incidencia ya procesada anteriormente."
        return state

    state = deterministic_router_phase.run(state)  # type: ignore[arg-type]

    if state.get("deterministic_decision") != "escalate_llm":
        _LOGGER.info(
            "[graph] execution=%s deterministic_decision=%s — skipping LLM phases",
            state["execution_id"],
            state.get("deterministic_decision"),
        )
        state["summary"] = build_summary(state)
        return state

    state = classify_phase.run(state)  # type: ignore[arg-type]

    if state["needs_heavy"]:
        state = escalate_phase.run(state)  # type: ignore[arg-type]

    state["summary"] = build_summary(state)
    return state
