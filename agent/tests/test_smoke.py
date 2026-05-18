"""Smoke tests for the ecommerce support agent backend.

Validates that: the package imports cleanly, FastAPI starts, the CLI arg
parser works, the graph routes correctly, schemas are valid JSON, and
the worker's queue loop behaves properly — all without a real DB or LLM.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import TracebackType
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import agent
from agent import api, cli, graph, worker
from agent.tools import ALLOWED_TOOLS_BY_PHASE, _allowed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides: Any) -> graph.State:
    """Build a minimal valid State for graph tests."""
    base: graph.State = {
        "execution_id": "exec-test",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "input": {"external_id": None},
        "summary": None,
        "light_output": None,
        "heavy_output": None,
        "incident_message": "No puedo acceder a la tienda",
        "reporter": "test-user",
        "channel": "web",
        "reported_at": "2026-05-12T10:00:00Z",
        "is_duplicate": False,
        "customer_context": None,
        "extracted_keywords": [],
        "initial_category": None,
        "initial_severity": None,
        "deterministic_decision": None,
        "deterministic_confidence": 0.0,
        "escalation_phone": None,
        "classification": None,
        "kb_results": [],
        "proposed_response": None,
        "needs_heavy": False,
        "ticket": None,
        "escalation_reason": None,
        "thread_id": None,
        "conversation_history": [],
        "final_response": None,
        "log_ref": None,
        "ticket_ref": None,
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


# ---------------------------------------------------------------------------
# Package meta
# ---------------------------------------------------------------------------

def test_package_version_is_pinned() -> None:
    assert agent.__version__ == "0.1.1"


def test_public_modules_import_cleanly() -> None:
    for name in (
        "agent.api",
        "agent.worker",
        "agent.cli",
        "agent.graph",
        "agent.phases.intake",
        "agent.phases.classify",
        "agent.phases.escalate",
        "agent.tools._allowed",
        "agent.services.clients.kb_client",
        "agent.services.clients.storage_client",
    ):
        importlib.import_module(name)


# ---------------------------------------------------------------------------
# FastAPI health + stubs
# ---------------------------------------------------------------------------

def test_health_endpoint_reports_db_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "unconfigured"}


def test_stub_endpoints_return_501() -> None:
    client = TestClient(api.app)
    assert client.post("/api/executions/abc/cancel").status_code == 501
    assert client.post("/api/issues/abc/resolve").status_code == 501


def test_create_incident_returns_503_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(api.app)
    payload = {
        "message": "El checkout no funciona",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "external_id": "test-ext-001",
        "reported_at": "2026-05-12T10:00:00Z",
        "reporter": "Operador Test",
        "channel": "web",
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 503


def test_create_incident_returns_422_for_missing_fields() -> None:
    client = TestClient(api.app)
    response = client.post("/api/incidents", json={"message": "incompleto"})
    assert response.status_code == 422


def test_create_incident_returns_422_for_empty_message() -> None:
    client = TestClient(api.app)
    payload = {
        "message": "",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "external_id": "test-ext-002",
        "reported_at": "2026-05-12T10:00:00Z",
        "reporter": "Operador Test",
        "channel": "web",
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 422


def test_get_incident_status_returns_503_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(api.app)
    response = client.get("/api/incidents/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_run_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="DATABASE_URL"):
        cli.main(["run", "--customer", "00000000-0000-0000-0000-000000000001"])


def test_cli_rejects_invalid_input_json() -> None:
    with pytest.raises(SystemExit, match="must be valid JSON"):
        cli.main(["run", "--customer", "00000000-0000-0000-0000-000000000001", "--input", "not-json"])


def test_cli_rejects_input_that_is_not_an_object() -> None:
    with pytest.raises(SystemExit, match="JSON object"):
        cli.main(["run", "--customer", "00000000-0000-0000-0000-000000000001", "--input", "[1, 2, 3]"])


def test_cli_retry_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="DATABASE_URL"):
        cli.main(["retry", "--execution", "00000000-0000-0000-0000-000000000999"])


# ---------------------------------------------------------------------------
# Graph routing
# ---------------------------------------------------------------------------

def test_graph_skips_llm_phases_on_duplicate() -> None:
    state = _make_state()

    def _intake_duplicate(s: dict[str, Any]) -> dict[str, Any]:
        s["is_duplicate"] = True
        return s

    with patch.object(graph.intake_phase, "run", side_effect=_intake_duplicate) as mock_intake, \
         patch.object(graph.classify_phase, "run") as mock_classify, \
         patch.object(graph.escalate_phase, "run") as mock_escalate:

        result = graph.run(state)

    mock_intake.assert_called_once()
    mock_classify.assert_not_called()
    mock_escalate.assert_not_called()
    assert result["final_response"] == "Incidencia ya procesada anteriormente."


def _det_escalate_llm(s: dict[str, Any]) -> dict[str, Any]:
    s["deterministic_decision"] = "escalate_llm"
    s["deterministic_confidence"] = 0.0
    s["escalation_phone"] = None
    return s


def test_graph_routes_to_heavy_when_classify_requests_it() -> None:
    state = _make_state()

    def _intake_ok(s: dict[str, Any]) -> dict[str, Any]:
        s["is_duplicate"] = False
        s["extracted_keywords"] = ["checkout"]
        return s

    def _classify_needs_heavy(s: dict[str, Any]) -> dict[str, Any]:
        s["needs_heavy"] = True
        s["classification"] = {"type": "payment", "severity": "critical", "confidence": 0.9}
        return s

    def _escalate_ok(s: dict[str, Any]) -> dict[str, Any]:
        s["final_response"] = "Escalado al equipo técnico."
        s["ticket_ref"] = "/Documentos/tickets/t.txt"
        s["log_ref"] = "/Documentos/logs/l.txt"
        return s

    with patch.object(graph.intake_phase, "run", side_effect=_intake_ok), \
         patch.object(graph.deterministic_router_phase, "run", side_effect=_det_escalate_llm), \
         patch.object(graph.classify_phase, "run", side_effect=_classify_needs_heavy), \
         patch.object(graph.escalate_phase, "run", side_effect=_escalate_ok) as mock_escalate:

        result = graph.run(state)

    mock_escalate.assert_called_once()
    assert result["summary"] is not None
    assert "type=payment" in result["summary"]


def test_graph_does_not_call_escalate_when_auto_resolved() -> None:
    state = _make_state()

    def _intake_ok(s: dict[str, Any]) -> dict[str, Any]:
        s["is_duplicate"] = False
        return s

    def _classify_auto_resolved(s: dict[str, Any]) -> dict[str, Any]:
        s["needs_heavy"] = False
        s["classification"] = {"type": "access", "severity": "medium", "confidence": 0.85}
        s["final_response"] = "Prueba a restablecer tu contraseña."
        s["log_ref"] = "/Documentos/logs/l.txt"
        return s

    with patch.object(graph.intake_phase, "run", side_effect=_intake_ok), \
         patch.object(graph.deterministic_router_phase, "run", side_effect=_det_escalate_llm), \
         patch.object(graph.classify_phase, "run", side_effect=_classify_auto_resolved), \
         patch.object(graph.escalate_phase, "run") as mock_escalate:

        result = graph.run(state)

    mock_escalate.assert_not_called()


def test_graph_stops_on_deterministic_resolve() -> None:
    state = _make_state()

    def _intake_ok(s: dict[str, Any]) -> dict[str, Any]:
        s["is_duplicate"] = False
        return s

    def _det_resolved(s: dict[str, Any]) -> dict[str, Any]:
        s["deterministic_decision"] = "resolved"
        s["deterministic_confidence"] = 0.85
        s["escalation_phone"] = None
        s["final_response"] = "Para restablecer tu contraseña..."
        s["needs_heavy"] = False
        s["classification"] = {"type": "access", "severity": "low", "confidence": 0.85}
        s["log_ref"] = "/Documentos/logs/l.txt"
        return s

    with patch.object(graph.intake_phase, "run", side_effect=_intake_ok), \
         patch.object(graph.deterministic_router_phase, "run", side_effect=_det_resolved), \
         patch.object(graph.classify_phase, "run") as mock_classify, \
         patch.object(graph.escalate_phase, "run") as mock_escalate:

        result = graph.run(state)

    mock_classify.assert_not_called()
    mock_escalate.assert_not_called()
    assert result["final_response"] == "Para restablecer tu contraseña..."
    assert "deterministic=resolved" in (result["summary"] or "")


def test_graph_stops_on_deterministic_human_escalation() -> None:
    state = _make_state()

    def _intake_ok(s: dict[str, Any]) -> dict[str, Any]:
        s["is_duplicate"] = False
        return s

    def _det_human(s: dict[str, Any]) -> dict[str, Any]:
        s["deterministic_decision"] = "escalate_human"
        s["deterministic_confidence"] = 0.95
        s["escalation_phone"] = "+34 910 555 111"
        s["final_response"] = "Equipo de atención: +34 910 555 111"
        s["needs_heavy"] = False
        s["classification"] = {"type": "complaint", "severity": "high", "confidence": 0.95}
        s["log_ref"] = "/Documentos/logs/l.txt"
        return s

    with patch.object(graph.intake_phase, "run", side_effect=_intake_ok), \
         patch.object(graph.deterministic_router_phase, "run", side_effect=_det_human), \
         patch.object(graph.classify_phase, "run") as mock_classify, \
         patch.object(graph.escalate_phase, "run") as mock_escalate:

        result = graph.run(state)

    mock_classify.assert_not_called()
    mock_escalate.assert_not_called()
    assert result["escalation_phone"] == "+34 910 555 111"
    assert "deterministic=escalate_human" in (result["summary"] or "")
    assert result["summary"] is not None


# ---------------------------------------------------------------------------
# build_summary
# ---------------------------------------------------------------------------

def test_build_summary_with_empty_classification() -> None:
    state = _make_state()
    result = graph.build_summary(state)
    assert "type=unknown" in result
    assert "severity=unknown" in result
    assert "confidence=0.00" in result
    assert "auto_resolved=True" in result


def test_build_summary_with_full_classification() -> None:
    state = _make_state(
        classification={"type": "payment", "severity": "critical", "confidence": 0.92},
        needs_heavy=True,
        log_ref="/Documentos/logs/abc.txt",
        ticket_ref="/Documentos/tickets/xyz.txt",
    )
    result = graph.build_summary(state)
    assert "type=payment" in result
    assert "severity=critical" in result
    assert "confidence=0.92" in result
    assert "auto_resolved=False" in result
    assert "log=" in result
    assert "ticket=" in result


# ---------------------------------------------------------------------------
# Tool whitelist
# ---------------------------------------------------------------------------

def test_whitelist_deterministic_phase() -> None:
    assert _allowed.is_tool_allowed("deterministic", "check_duplicate") is True
    assert _allowed.is_tool_allowed("deterministic", "get_customer_context") is True
    assert _allowed.is_tool_allowed("deterministic", "write_log") is True
    assert _allowed.is_tool_allowed("deterministic", "search_knowledge_base") is False
    assert _allowed.is_tool_allowed("deterministic", "create_ticket") is False


def test_whitelist_light_llm_phase() -> None:
    assert _allowed.is_tool_allowed("light_llm", "search_knowledge_base") is True
    assert _allowed.is_tool_allowed("light_llm", "write_log") is True
    assert _allowed.is_tool_allowed("light_llm", "get_recent_incidents") is True
    assert _allowed.is_tool_allowed("light_llm", "create_ticket") is False
    assert _allowed.is_tool_allowed("light_llm", "check_duplicate") is False


def test_whitelist_heavy_llm_phase() -> None:
    assert _allowed.is_tool_allowed("heavy_llm", "create_ticket") is True
    assert _allowed.is_tool_allowed("heavy_llm", "search_knowledge_base") is True
    assert _allowed.is_tool_allowed("heavy_llm", "write_log") is True
    assert _allowed.is_tool_allowed("heavy_llm", "check_duplicate") is False


def test_whitelist_unknown_phase_returns_false() -> None:
    assert _allowed.is_tool_allowed("unknown_phase", "any_tool") is False
    assert ALLOWED_TOOLS_BY_PHASE.get("unknown_phase") is None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("schema_name", ["input.schema.json", "output.schema.json"])
def test_schemas_are_valid_json_with_strict_additional_properties(schema_name: str) -> None:
    schema_path = Path(agent.__file__).parent / "schemas" / schema_name
    data: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data["$schema"].startswith("https://json-schema.org/")
    assert data.get("additionalProperties") is False


# ---------------------------------------------------------------------------
# Example payload
# ---------------------------------------------------------------------------

def test_example_payload_is_valid_json() -> None:
    example_path = Path(agent.__file__).parent / "examples" / "checkout_incident.json"
    data: dict[str, Any] = json.loads(example_path.read_text(encoding="utf-8"))
    assert data["input"]["customer_id"]
    assert data["input"]["message"]
    assert data["expected"]["output"]["auto_resolved"] is False
    assert data["expected"]["phase_deterministic"]["initial_severity"] == "critical"


# ---------------------------------------------------------------------------
# Prompt files
# ---------------------------------------------------------------------------

def test_prompt_files_have_valid_frontmatter() -> None:
    """Each prompt file must have front-matter with model, max_tokens, and template variables."""
    prompts_dir = Path(agent.__file__).parent / "prompts"
    prompt_files = [p for p in prompts_dir.glob("*.md") if not p.name.startswith("_")]
    assert prompt_files, "no prompt files found in agent/prompts/"

    required_keys = {"model", "max_tokens", "temperature"}
    for prompt_file in prompt_files:
        text = prompt_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{prompt_file.name} must start with YAML front-matter"
        fm_end = text.index("---", 3)
        frontmatter = text[3:fm_end]
        for key in required_keys:
            assert f"{key}:" in frontmatter, f"{prompt_file.name} missing '{key}' in front-matter"


# ---------------------------------------------------------------------------
# Worker: handle_execution warns without DATABASE_URL
# ---------------------------------------------------------------------------

def test_worker_handle_execution_warns_when_database_url_unset(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with caplog.at_level("WARNING", logger="agent.worker"):
        worker._handle_execution("exec-1")
    assert any(
        "DATABASE_URL unset" in r.getMessage() and "exec-1" in r.getMessage()
        for r in caplog.records
    )


def test_worker_main_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        worker.main()


# ---------------------------------------------------------------------------
# Worker: _claim_one (fake connection)
# ---------------------------------------------------------------------------


class _FakeCursor:
    def __init__(self, fetch_result: tuple[Any, ...] | None) -> None:
        self._fetch_result = fetch_result
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        self.executed.append((query, params))

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._fetch_result

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class _FakeConnection:
    def __init__(self, fetch_result: tuple[Any, ...] | None) -> None:
        self._cursor = _FakeCursor(fetch_result)
        self.commits = 0

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.commits += 1


def test_worker_claim_one_returns_locked_execution_id() -> None:
    fake_conn = _FakeConnection(fetch_result=("00000000-0000-0000-0000-000000000123",))
    result = worker._claim_one(fake_conn)  # type: ignore[arg-type]
    assert result == "00000000-0000-0000-0000-000000000123"
    assert fake_conn.commits == 1
    query, params = fake_conn._cursor.executed[0]
    assert "UPDATE queue" in query
    assert params == (worker._LOCK_OWNER,)


def test_worker_claim_one_returns_none_when_queue_empty() -> None:
    fake_conn = _FakeConnection(fetch_result=None)
    assert worker._claim_one(fake_conn) is None  # type: ignore[arg-type]
    assert fake_conn.commits == 1
