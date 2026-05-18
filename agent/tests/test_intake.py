"""Unit tests for agent.phases.intake (phase_deterministic).

All DB calls (check_duplicate, get_customer_context) are mocked so these
tests run without a real Postgres connection.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from agent.phases import intake
from agent.phases.intake import _classify_severity, _classify_type, _extract_keywords


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "execution_id": "exec-intake-test",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "input": {"external_id": "ext-001"},
        "incident_message": "No puedo acceder al checkout para pagar",
        "reporter": "test-user",
        "channel": "web",
        "reported_at": "2026-05-12T10:00:00Z",
        "is_duplicate": False,
        "customer_context": None,
        "extracted_keywords": [],
        "initial_category": None,
        "initial_severity": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _extract_keywords
# ---------------------------------------------------------------------------

def test_extract_keywords_removes_stop_words() -> None:
    result = _extract_keywords("no puedo acceder al login de la tienda")
    assert "acceder" in result
    assert "login" in result
    assert "tienda" in result
    # stop words must be absent
    for stop in ("no", "al", "de", "la"):
        assert stop not in result


def test_extract_keywords_deduplicates() -> None:
    result = _extract_keywords("checkout checkout pagar pagar tarjeta")
    assert result.count("checkout") == 1
    assert result.count("pagar") == 1


def test_extract_keywords_limits_to_12() -> None:
    long_text = " ".join(f"palabra{i}" for i in range(20))
    result = _extract_keywords(long_text)
    assert len(result) <= 12


def test_extract_keywords_skips_words_shorter_than_3_chars() -> None:
    result = _extract_keywords("no va ok tienda")
    # "no", "va", "ok" are ≤2 chars; "tienda" is 6 chars and not a stop word
    assert "tienda" in result
    assert "va" not in result
    assert "ok" not in result


def test_extract_keywords_empty_text_returns_empty_list() -> None:
    assert _extract_keywords("") == []


# ---------------------------------------------------------------------------
# _classify_severity
# ---------------------------------------------------------------------------

def test_classify_severity_checkout_is_critical() -> None:
    assert _classify_severity("El checkout no funciona, no podemos pagar") == "critical"


def test_classify_severity_login_is_critical() -> None:
    assert _classify_severity("No puedo acceder a mi cuenta, falla el login") == "critical"


def test_classify_severity_images_is_high() -> None:
    assert _classify_severity("Las imágenes del producto no cargan") == "high"


def test_classify_severity_coupon_is_medium() -> None:
    assert _classify_severity("El cupón de descuento no aplica") == "medium"


def test_classify_severity_description_is_low() -> None:
    assert _classify_severity("La descripción del producto tiene una errata") == "low"


def test_classify_severity_returns_none_for_unrecognised_text() -> None:
    assert _classify_severity("Todo parece funcionar bien hoy") is None


# ---------------------------------------------------------------------------
# _classify_type
# ---------------------------------------------------------------------------

def test_classify_type_payment_keywords() -> None:
    assert _classify_type("No se puede completar el checkout con tarjeta") == "payment"


def test_classify_type_access_keywords() -> None:
    assert _classify_type("Problema con el login y la contraseña") == "access"


def test_classify_type_content_keywords() -> None:
    assert _classify_type("La imagen del producto no aparece") == "content"


def test_classify_type_functional_keywords() -> None:
    assert _classify_type("El cupón de descuento no funciona en el carrito") == "functional"


def test_classify_type_technical_keywords() -> None:
    assert _classify_type("Error 500 en la web, carga muy lenta") == "technical"


def test_classify_type_returns_none_for_unrecognised_text() -> None:
    assert _classify_type("Me gusta mucho esta tienda") is None


# ---------------------------------------------------------------------------
# intake.run() — happy path
# ---------------------------------------------------------------------------

def test_run_happy_path_sets_keywords_and_classification() -> None:
    state = _make_state(incident_message="El checkout no deja pagar con tarjeta")

    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value={"name": "Tienda Test"}):
        result = intake.run(state)

    assert result["is_duplicate"] is False
    assert "checkout" in result["extracted_keywords"] or "pagar" in result["extracted_keywords"]
    assert result["initial_severity"] == "critical"
    assert result["initial_category"] == "payment"
    assert result["customer_context"] == {"name": "Tienda Test"}


def test_run_happy_path_without_external_id() -> None:
    state = _make_state(incident_message="Las imágenes no cargan")
    state["input"] = {"external_id": None}

    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value=None):
        result = intake.run(state)

    assert result["is_duplicate"] is False
    assert result["initial_severity"] == "high"


# ---------------------------------------------------------------------------
# intake.run() — duplicate detection
# ---------------------------------------------------------------------------

def test_run_returns_early_on_duplicate() -> None:
    state = _make_state(incident_message="El checkout falla")

    with patch("agent.phases.intake.check_duplicate", return_value=True) as mock_dup, \
         patch("agent.phases.intake.get_customer_context") as mock_ctx:
        result = intake.run(state)

    assert result["is_duplicate"] is True
    mock_dup.assert_called_once()
    mock_ctx.assert_not_called()
    # No keywords should be extracted on duplicate path
    assert result["extracted_keywords"] == []


# ---------------------------------------------------------------------------
# intake.run() — input validation
# ---------------------------------------------------------------------------

def test_run_raises_on_empty_message() -> None:
    state = _make_state(incident_message="")
    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value=None):
        with pytest.raises(ValueError, match="empty"):
            intake.run(state)


def test_run_raises_on_whitespace_only_message() -> None:
    state = _make_state(incident_message="   ")
    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value=None):
        with pytest.raises(ValueError, match="empty"):
            intake.run(state)


def test_run_raises_on_message_over_2000_chars() -> None:
    state = _make_state(incident_message="a" * 2001)
    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value=None):
        with pytest.raises(ValueError, match="too long"):
            intake.run(state)


def test_run_accepts_message_of_exactly_2000_chars() -> None:
    state = _make_state(incident_message="x" * 2000)
    with patch("agent.phases.intake.check_duplicate", return_value=False), \
         patch("agent.phases.intake.get_customer_context", return_value=None):
        result = intake.run(state)
    assert result["is_duplicate"] is False


# ---------------------------------------------------------------------------
# Tool defence-in-depth: check_duplicate raises on wrong phase
# ---------------------------------------------------------------------------

def test_check_duplicate_raises_when_called_from_wrong_phase() -> None:
    from agent.tools.check_duplicate import check_duplicate
    with pytest.raises(PermissionError, match="not allowed"):
        check_duplicate("light_llm", "cust-1", "ext-1", "exec-1")
