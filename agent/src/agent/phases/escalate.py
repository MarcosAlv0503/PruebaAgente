"""Phase 3 — heavy_llm: deep analysis with sonnet, ticket generation."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agent._logging import get_logger
from agent.services import llm_client
from agent.tools.create_ticket import create_ticket
from agent.tools.search_knowledge_base import search_knowledge_base
from agent.tools.write_log import write_log

_LOGGER = get_logger("phase.escalate")
_PHASE = "heavy_llm"
_PROMPT_FILE = Path(__file__).parents[1] / "prompts" / "escalator-v1-2026-05-12.md"


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Deep analysis with sonnet. Generates ticket + log + escalation response.

    Called only when phase_light_llm sets needs_heavy=True.
    Always writes both a ticket and a log regardless of analysis outcome.
    """
    execution_id: str = str(state["execution_id"])
    message: str = str(state.get("incident_message", ""))
    keywords: list[str] = list(state.get("extracted_keywords", []))
    escalation_reason: str = str(state.get("escalation_reason", "insufficient_confidence"))
    initial_classification: dict[str, Any] = state.get("classification") or {}

    _LOGGER.info("[phase.escalate] execution=%s reason=%s", execution_id, escalation_reason)

    kb_results = search_knowledge_base(_PHASE, keywords, top_k=5)

    prompt = llm_client.load_prompt(_PROMPT_FILE)

    user_content = (
        prompt.body
        .replace("{incident_message}", message)
        .replace("{kb_excerpts}", _format_kb_excerpts(kb_results))
        .replace("{initial_classification}", json.dumps(initial_classification, ensure_ascii=False))
        .replace("{escalation_reason}", escalation_reason)
    )

    conversation_history: list[dict[str, str]] = list(state.get("conversation_history") or [])
    messages = _build_messages(conversation_history, user_content)

    response_text = llm_client.chat(
        model=os.environ.get("MODEL_HEAVY", prompt.model),
        messages=messages,
        max_tokens=prompt.max_tokens,
        temperature=prompt.temperature,
        execution_id=execution_id,
    )

    result = _parse_llm_response(response_text)

    incident_type = str(result.get("type", initial_classification.get("type", "other")))
    severity = str(result.get("severity", initial_classification.get("severity", "medium")))
    confidence = float(result.get("confidence", 0.5))
    summary = str(result.get("summary", f"Incidencia {incident_type} requiere revisión"))
    context_text = str(result.get("context", ""))
    escalation_reason_final = str(result.get("escalation_reason", escalation_reason))
    suggested_steps = str(result.get("suggested_steps", "Revisar manualmente la incidencia."))
    final_response = str(result.get("response", "Tu incidencia ha sido escalada al equipo técnico."))

    state["classification"] = {
        "type": incident_type,
        "severity": severity,
        "confidence": confidence,
    }
    state["heavy_output"] = result
    state["ticket"] = {
        "summary": summary,
        "priority": severity,
        "escalation_reason": escalation_reason_final,
    }

    state["ticket_ref"] = create_ticket(
        _PHASE,
        execution_id=execution_id,
        priority=severity,
        summary=summary,
        reporter=str(state.get("reporter", "unknown")),
        incident_message=message,
        context=context_text,
        escalation_reason=escalation_reason_final,
        suggested_steps=suggested_steps,
    )

    state["log_ref"] = write_log(
        _PHASE,
        incident_id=execution_id,
        execution_id=execution_id,
        reporter=str(state.get("reporter", "unknown")),
        channel=str(state.get("channel", "web")),
        incident_type=incident_type,
        severity=severity,
        confidence=confidence,
        auto_resolved=False,
        message=message,
        response=final_response,
        kb_refs=[str(r.get("path", "")) for r in kb_results],
    )

    state["final_response"] = final_response

    _LOGGER.info(
        "[phase.escalate] execution=%s ticket_ref=%s log_ref=%s",
        execution_id,
        state["ticket_ref"],
        state["log_ref"],
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
        f"[{i}] {r.get('title', 'Sin título')}\n{str(r.get('excerpt', ''))[:400]}"
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
        _LOGGER.warning("[phase.escalate] LLM response is not valid JSON — using fallback")
        return {
            "type": "other",
            "severity": "medium",
            "confidence": 0.5,
            "summary": "Incidencia requiere revisión manual",
            "context": "El análisis automático no pudo completarse correctamente.",
            "escalation_reason": "llm_parse_error",
            "suggested_steps": "Revisar el mensaje original y clasificar manualmente.",
            "response": "Tu incidencia ha sido escalada al equipo técnico para revisión.",
        }
