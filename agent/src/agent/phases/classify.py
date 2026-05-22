"""Phase 2 — light_llm: classify with haiku, search KB, auto-resolve or flag for escalation."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agent._logging import get_logger
from agent.services import llm_client
from agent.tools.search_knowledge_base import search_knowledge_base
from agent.tools.write_log import write_log

_LOGGER = get_logger("phase.classify")
_PHASE = "light_llm"
_PROMPT_FILE = Path(__file__).parents[1] / "prompts" / "classifier-v2-2026-05-20.md"


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Classify with haiku + KB search. Writes log and sets final_response if auto-resolved.

    If confidence < CONFIDENCE_THRESHOLD or KB has no match, sets needs_heavy=True.
    The LLM prompt already enforces that critical severity → auto_resolvable=false,
    so severity is not checked here to avoid double-penalising over-classified inputs.
    """
    execution_id: str = str(state["execution_id"])
    message: str = str(state.get("incident_message", ""))
    keywords: list[str] = list(state.get("extracted_keywords", []))
    initial_severity: str | None = state.get("initial_severity")

    _LOGGER.info("[phase.classify] execution=%s keywords=%s", execution_id, keywords)

    kb_results = search_knowledge_base(_PHASE, keywords, top_k=3)
    state["kb_results"] = kb_results

    prompt = llm_client.load_prompt(_PROMPT_FILE)

    user_content = (
        prompt.body
        .replace("{incident_message}", message)
        .replace("{kb_excerpts}", _format_kb_excerpts(kb_results))
        .replace("{initial_severity}", initial_severity or "desconocida")
    )

    conversation_history: list[dict[str, str]] = list(state.get("conversation_history") or [])
    messages = _build_messages(conversation_history, user_content)

    response_text = llm_client.chat(
        model=os.environ.get("MODEL_LIGHT", prompt.model),
        messages=messages,
        max_tokens=prompt.max_tokens,
        temperature=prompt.temperature,
        execution_id=execution_id,
    )

    result = _parse_llm_response(response_text)

    confidence = float(result.get("confidence", 0.0))
    incident_type = str(result.get("type", state.get("initial_category") or "other"))
    severity = str(result.get("severity", initial_severity or "medium"))
    auto_resolvable = bool(result.get("auto_resolvable", False))

    threshold = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.75"))

    if confidence < threshold or not kb_results:
        auto_resolvable = False

    state["classification"] = {
        "type": incident_type,
        "severity": severity,
        "confidence": confidence,
    }
    state["light_output"] = {"type": incident_type, "severity": severity, "confidence": confidence}

    if auto_resolvable:
        response_body = str(result.get("response", ""))
        state["proposed_response"] = response_body
        state["final_response"] = response_body
        state["needs_heavy"] = False

        state["log_ref"] = write_log(
            _PHASE,
            incident_id=execution_id,
            execution_id=execution_id,
            reporter=str(state.get("reporter", "unknown")),
            channel=str(state.get("channel", "web")),
            incident_type=incident_type,
            severity=severity,
            confidence=confidence,
            auto_resolved=True,
            message=message,
            response=response_body,
            kb_refs=[str(r.get("path", "")) for r in kb_results],
        )
        _LOGGER.info("[phase.classify] execution=%s auto_resolved=true type=%s", execution_id, incident_type)
    else:
        state["needs_heavy"] = True
        state["escalation_reason"] = str(result.get("escalation_reason", "insufficient_confidence"))
        _LOGGER.info(
            "[phase.classify] execution=%s needs_heavy=true reason=%s",
            execution_id,
            state["escalation_reason"],
        )

    return state


def _build_messages(
    history: list[dict[str, str]], current_user_content: str
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = list(history)
    messages.append({"role": "user", "content": current_user_content})
    return messages


def _format_kb_excerpts(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No se encontraron documentos relevantes en la base de conocimiento."
    parts = [
        f"[{i}] {r.get('title', 'Sin título')} (relevancia: {r.get('score', 0)})\n{str(r.get('excerpt', ''))[:400]}"
        for i, r in enumerate(results, 1)
    ]
    return "\n\n---\n\n".join(parts)


def _parse_llm_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        result: dict[str, Any] = json.loads(text)
        return result
    except (json.JSONDecodeError, ValueError):
        _LOGGER.warning("[phase.classify] LLM response is not valid JSON — forcing escalation")
        return {
            "type": "other",
            "severity": "medium",
            "confidence": 0.0,
            "auto_resolvable": False,
            "escalation_reason": "llm_parse_error",
        }
