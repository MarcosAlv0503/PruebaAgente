"""Unit tests for agent.services.clients.storage_client.

Redirects all filesystem writes to a pytest tmp_path by monkeypatching
the module-level _LOGS_DIR and _TICKETS_DIR constants.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent.services.clients import storage_client


@pytest.fixture(autouse=True)
def _patch_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect writes to a temporary directory for every test in this module."""
    monkeypatch.setattr(storage_client, "_LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(storage_client, "_TICKETS_DIR", tmp_path / "tickets")


# ---------------------------------------------------------------------------
# write_log
# ---------------------------------------------------------------------------

def test_write_log_creates_file(tmp_path: Path) -> None:
    ref = storage_client.write_log(
        incident_id="inc-001",
        execution_id="exec-001",
        reporter="María García",
        channel="web",
        incident_type="payment",
        severity="critical",
        confidence=0.92,
        auto_resolved=False,
        message="El checkout no funciona",
        response="Escalado al equipo técnico.",
        kb_refs=["knowledge/faqs/checkout.md"],
    )
    assert Path(ref).exists()


def test_write_log_creates_logs_directory_when_missing(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    assert not logs_dir.exists()
    storage_client.write_log(
        incident_id="inc-002",
        execution_id="exec-002",
        reporter="test",
        channel="web",
        incident_type="technical",
        severity="high",
        confidence=0.8,
        auto_resolved=True,
        message="Error 500",
        response="Reinicia la caché.",
        kb_refs=[],
    )
    assert logs_dir.exists()


def test_write_log_filename_contains_incident_id_and_type(tmp_path: Path) -> None:
    ref = storage_client.write_log(
        incident_id="myincident123",
        execution_id="exec-003",
        reporter="test",
        channel="web",
        incident_type="access",
        severity="medium",
        confidence=0.85,
        auto_resolved=True,
        message="No puedo entrar",
        response="Restablece la contraseña.",
        kb_refs=[],
    )
    filename = Path(ref).name
    assert "myincident123" in filename
    assert "access" in filename


def test_write_log_content_contains_required_fields(tmp_path: Path) -> None:
    ref = storage_client.write_log(
        incident_id="inc-004",
        execution_id="exec-004",
        reporter="Carlos López",
        channel="web",
        incident_type="functional",
        severity="low",
        confidence=0.78,
        auto_resolved=True,
        message="El filtro de tallas no funciona",
        response="Intenta recargar la página.",
        kb_refs=["knowledge/faqs/filtros.md"],
    )
    content = Path(ref).read_text(encoding="utf-8")
    assert "inc-004" in content
    assert "exec-004" in content
    assert "Carlos López" in content
    assert "functional" in content
    assert "low" in content
    assert "0.780" in content
    assert "El filtro de tallas" in content
    assert "knowledge/faqs/filtros.md" in content


def test_write_log_shows_none_kb_refs_when_empty(tmp_path: Path) -> None:
    ref = storage_client.write_log(
        incident_id="inc-005",
        execution_id="exec-005",
        reporter="test",
        channel="web",
        incident_type="other",
        severity="medium",
        confidence=0.5,
        auto_resolved=False,
        message="Algo extraño",
        response="",
        kb_refs=[],
    )
    content = Path(ref).read_text(encoding="utf-8")
    assert "none" in content


def test_write_log_returns_string_path() -> None:
    ref = storage_client.write_log(
        incident_id="inc-006",
        execution_id="exec-006",
        reporter="test",
        channel="web",
        incident_type="technical",
        severity="high",
        confidence=0.9,
        auto_resolved=False,
        message="Error",
        response="",
        kb_refs=[],
    )
    assert isinstance(ref, str)
    assert len(ref) > 0


# ---------------------------------------------------------------------------
# write_ticket
# ---------------------------------------------------------------------------

def test_write_ticket_creates_file(tmp_path: Path) -> None:
    ref = storage_client.write_ticket(
        execution_id="exec-010",
        priority="critical",
        summary="Checkout bloqueado",
        reporter="María García",
        incident_message="El checkout no deja pagar",
        context="Tienda sin ventas desde las 10:00",
        escalation_reason="critical_severity",
        suggested_steps="Revisar logs del gateway de pago",
    )
    assert Path(ref).exists()


def test_write_ticket_filename_contains_priority(tmp_path: Path) -> None:
    ref = storage_client.write_ticket(
        execution_id="exec-011",
        priority="high",
        summary="Imágenes caídas",
        reporter="test",
        incident_message="Las fotos no cargan",
        context="Afecta a toda la galería",
        escalation_reason="insufficient_confidence",
        suggested_steps="Revisar CDN",
    )
    filename = Path(ref).name
    assert "high" in filename


def test_write_ticket_content_contains_required_fields(tmp_path: Path) -> None:
    ref = storage_client.write_ticket(
        execution_id="exec-012",
        priority="critical",
        summary="Pasarela de pago caída",
        reporter="Ana Martínez",
        incident_message="No se puede completar ningún pedido",
        context="Todas las tarjetas son rechazadas",
        escalation_reason="critical_payment_failure",
        suggested_steps="1. Contactar con Stripe. 2. Activar pasarela de backup.",
    )
    content = Path(ref).read_text(encoding="utf-8")
    assert "exec-012" in content
    assert "critical" in content
    assert "Pasarela de pago caída" in content
    assert "Ana Martínez" in content
    assert "critical_payment_failure" in content
    assert "Stripe" in content


def test_write_ticket_returns_string_path() -> None:
    ref = storage_client.write_ticket(
        execution_id="exec-013",
        priority="medium",
        summary="Test",
        reporter="test",
        incident_message="Test message",
        context="Test context",
        escalation_reason="test_reason",
        suggested_steps="Test steps",
    )
    assert isinstance(ref, str)
    assert len(ref) > 0


def test_write_ticket_each_call_creates_unique_file(tmp_path: Path) -> None:
    kwargs = dict(
        execution_id="exec-014",
        priority="low",
        summary="Test",
        reporter="test",
        incident_message="Mensaje",
        context="Contexto",
        escalation_reason="reason",
        suggested_steps="Steps",
    )
    ref1 = storage_client.write_ticket(**kwargs)  # type: ignore[arg-type]
    ref2 = storage_client.write_ticket(**kwargs)  # type: ignore[arg-type]
    assert ref1 != ref2
