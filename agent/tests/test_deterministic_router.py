"""Tests for the deterministic rule engine and router phase.

All tests are pure Python — no DB, no LLM, no filesystem writes.
The router phase tests mock write_log to stay side-effect-free.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from agent.rules import rule_engine
from agent.rules.rule_engine import MatchResult


# ---------------------------------------------------------------------------
# rule_engine.match — auto-resolve cases
# ---------------------------------------------------------------------------

def test_password_reset_matches():
    result = rule_engine.match("olvidé mi contraseña y no puedo entrar")
    assert result.decision == "resolved"
    assert result.rule_id == "password_reset"
    assert result.confidence >= 0.40


def test_order_tracking_matches():
    result = rule_engine.match("¿dónde está mi pedido? quiero ver el seguimiento")
    assert result.decision == "resolved"
    assert result.rule_id == "order_tracking"


def test_return_policy_matches():
    result = rule_engine.match("¿cuál es la política de devolución? cómo devuelvo un artículo")
    assert result.decision == "resolved"
    assert result.rule_id == "return_policy"


def test_size_guide_matches():
    result = rule_engine.match("no sé qué talla me pongo, ¿hay guía de tallas?")
    assert result.decision == "resolved"
    assert result.rule_id == "size_guide"


def test_coupon_bienvenido10_matches():
    result = rule_engine.match("el cupón BIENVENIDO10 no me funciona")
    assert result.decision == "resolved"
    assert result.rule_id == "coupon_bienvenido10"


# ---------------------------------------------------------------------------
# rule_engine.match — human escalation cases
# ---------------------------------------------------------------------------

def test_duplicate_charge_escalates_to_human():
    result = rule_engine.match("me han cobrado dos veces el mismo pedido")
    assert result.decision == "escalate_human"
    assert result.rule_id == "duplicate_charge"
    assert result.escalation_phone == "+34 910 555 111"


def test_defective_product_escalates_to_human():
    result = rule_engine.match("el artículo llegó roto, en mal estado")
    assert result.decision == "escalate_human"
    assert result.rule_id == "defective_product"


def test_formal_complaint_escalates_to_human():
    result = rule_engine.match("quiero presentar una reclamación formal")
    assert result.decision == "escalate_human"
    assert result.rule_id == "formal_complaint"


# ---------------------------------------------------------------------------
# rule_engine.match — LLM fallback
# ---------------------------------------------------------------------------

def test_unknown_message_falls_through_to_llm():
    result = rule_engine.match("tengo un problema muy extraño con mi cuenta que no sé cómo describir")
    assert result.decision == "escalate_llm"
    assert result.rule_id is None
    assert result.confidence == 0.0


def test_empty_message_falls_through_to_llm():
    result = rule_engine.match("hola")
    assert result.decision == "escalate_llm"


# ---------------------------------------------------------------------------
# rule_engine.match — negation handling
# ---------------------------------------------------------------------------

def test_negation_lowers_score_below_resolve_threshold():
    # "no quiero devolver" should NOT trigger return_policy auto-resolve
    result = rule_engine.match("no quiero devolver nada, el pedido está bien")
    # Either falls to LLM or escalates, but should NOT auto-resolve as a return request
    assert result.decision != "resolved" or (result.rule_id != "return_policy")


# ---------------------------------------------------------------------------
# deterministic_router phase integration
# ---------------------------------------------------------------------------

def _make_state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "execution_id": "exec-det-test",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "input": {},
        "incident_message": "",
        "reporter": "test",
        "channel": "web",
        "initial_category": None,
        "initial_severity": None,
        "deterministic_decision": None,
        "deterministic_confidence": 0.0,
        "escalation_phone": None,
        "needs_heavy": False,
        "final_response": None,
        "log_ref": None,
    }
    base.update(overrides)
    return base


def test_router_phase_resolved_sets_state():
    from agent.phases import deterministic_router

    state = _make_state(incident_message="olvidé mi contraseña, cómo la reseteo")

    with patch("agent.phases.deterministic_router.write_log", return_value="/Documentos/logs/x.txt"):
        result = deterministic_router.run(state)

    assert result["deterministic_decision"] == "resolved"
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 10
    assert result["needs_heavy"] is False
    assert result["log_ref"] == "/Documentos/logs/x.txt"


def test_router_phase_human_escalation_includes_phone():
    from agent.phases import deterministic_router

    state = _make_state(incident_message="me han cobrado dos veces el mismo pedido")

    with patch("agent.phases.deterministic_router.write_log", return_value="/Documentos/logs/y.txt"):
        result = deterministic_router.run(state)

    assert result["deterministic_decision"] == "escalate_human"
    assert result["escalation_phone"] == "+34 910 555 111"
    assert "+34 910 555 111" in (result["final_response"] or "")
    assert result["needs_heavy"] is False


def test_router_phase_llm_fallback_leaves_state_clean():
    from agent.phases import deterministic_router

    state = _make_state(incident_message="algo muy raro y específico que no encaja en ninguna regla")

    with patch("agent.phases.deterministic_router.write_log") as mock_log:
        result = deterministic_router.run(state)

    assert result["deterministic_decision"] == "escalate_llm"
    assert result["final_response"] is None
    assert result["needs_heavy"] is False
    mock_log.assert_not_called()
