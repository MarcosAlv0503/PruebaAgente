"""Smoke tests for the template-agent backend.

The point of these tests is to fail loud if a clone of the template lands in
a state where the package no longer imports, the FastAPI app cannot start,
the CLI argparse is broken, the graph stub diverges from the documented
shape, or the JSON schemas drift away from being valid JSON. They run
without docker because we mock the database probe.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest
from fastapi.testclient import TestClient
from loang_toolkit import PromptLoader

import agent
from agent import api, cli, graph, worker
from agent.phases import _example as phase_example
from agent.tools import ALLOWED_TOOLS_BY_PHASE, _allowed


def test_package_version_is_pinned() -> None:
    assert agent.__version__ == "0.1.1"


def test_public_modules_import_cleanly() -> None:
    for name in (
        "agent.api",
        "agent.worker",
        "agent.cli",
        "agent.graph",
        "agent.phases._example",
        "agent.tools._allowed",
        "agent.services.clients",
    ):
        importlib.import_module(name)


def test_health_endpoint_reports_db_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "db": "unconfigured"}


def test_stub_endpoints_return_501() -> None:
    client = TestClient(api.app)
    assert client.post("/api/executions/abc/cancel").status_code == 501
    assert client.post("/api/issues/abc/resolve").status_code == 501


def test_cli_run_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="DATABASE_URL"):
        cli.main(["run", "--customer", "00000000-0000-0000-0000-000000000001"])


def test_cli_rejects_invalid_input_json() -> None:
    with pytest.raises(SystemExit, match="must be valid JSON"):
        cli.main(
            [
                "run",
                "--customer",
                "00000000-0000-0000-0000-000000000001",
                "--input",
                "not-json",
            ]
        )


def test_cli_rejects_input_that_is_not_an_object() -> None:
    with pytest.raises(SystemExit, match="JSON object"):
        cli.main(
            [
                "run",
                "--customer",
                "00000000-0000-0000-0000-000000000001",
                "--input",
                "[1, 2, 3]",
            ]
        )


def test_cli_retry_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="DATABASE_URL"):
        cli.main(["retry", "--execution", "00000000-0000-0000-0000-000000000999"])


def test_graph_runs_three_phases_in_order() -> None:
    state: graph.State = {
        "execution_id": "exec-1",
        "customer_id": "cust-1",
        "input": {},
        "summary": None,
        "light_output": None,
        "heavy_output": None,
    }
    result = graph.run(state)
    assert result["summary"] == "deterministic-stub"
    assert result["light_output"] == {"stub": True}
    assert result["heavy_output"] is None  # gated by needs_heavy flag


def test_phase_heavy_llm_populates_heavy_output() -> None:
    state: graph.State = {
        "execution_id": "exec-1",
        "customer_id": "cust-1",
        "input": {},
        "summary": None,
        "light_output": None,
        "heavy_output": None,
    }
    result = graph.phase_heavy_llm(state)
    assert result["heavy_output"] == {"stub": True}


def test_build_summary_handles_empty_state() -> None:
    state: graph.State = {
        "execution_id": "x",
        "customer_id": "y",
        "input": {},
        "summary": None,
        "light_output": None,
        "heavy_output": None,
    }
    assert graph.build_summary(state) == "(empty)"


def test_build_summary_concatenates_filled_state() -> None:
    state: graph.State = {
        "execution_id": "x",
        "customer_id": "y",
        "input": {},
        "summary": "ok",
        "light_output": {"a": 1},
        "heavy_output": {"b": 2},
    }
    out = graph.build_summary(state)
    assert "summary=ok" in out
    assert "light=" in out
    assert "heavy=" in out


def test_tool_whitelist_is_empty_until_project_fills_it() -> None:
    assert _allowed.is_tool_allowed("light_llm", "search") is False
    assert ALLOWED_TOOLS_BY_PHASE["deterministic"] == frozenset()
    assert ALLOWED_TOOLS_BY_PHASE["light_llm"] == frozenset()
    assert ALLOWED_TOOLS_BY_PHASE["heavy_llm"] == frozenset()


@pytest.mark.parametrize(
    "schema_name",
    ["input.schema.json", "output.schema.json"],
)
def test_schemas_are_valid_json_with_strict_additional_properties(schema_name: str) -> None:
    schema_path = Path(agent.__file__).parent / "schemas" / schema_name
    data: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data["$schema"].startswith("https://json-schema.org/")
    assert data.get("additionalProperties") is False


def test_example_payload_is_valid_json() -> None:
    example_path = Path(agent.__file__).parent / "examples" / "_example.json"
    data = json.loads(example_path.read_text(encoding="utf-8"))
    assert data["input"]["customer_id"]
    assert data["output"]["status"] == "succeeded"


def test_example_prompt_loads_via_loang_toolkit() -> None:
    """The example prompt's front-matter is the contract every project clone
    inherits; if it stops being parseable, every project breaks."""
    prompts_dir = Path(agent.__file__).parent / "prompts"
    prompt_file = next(prompts_dir.glob("*.md"))
    prompt = PromptLoader().load(prompt_file)
    assert prompt.name == "example"
    assert prompt.max_tokens == 16000


def test_phase_example_is_identity() -> None:
    state: dict[str, Any] = {"foo": "bar"}
    assert phase_example.run(state) == state


def test_worker_handle_execution_warns_when_database_url_unset(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ``DATABASE_URL`` the stub cannot close the lifecycle, so it
    emits a clear warning instead of silently doing nothing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with caplog.at_level("WARNING", logger="agent.worker"):
        worker._handle_execution("exec-1")
    assert any(
        "DATABASE_URL unset" in record.message and "exec-1" in record.message
        for record in caplog.records
    )


def test_worker_main_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        worker.main()


# --- _claim_one fakes ------------------------------------------------------


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


def _drain_iterator(it: Iterator[Any]) -> None:
    for _ in it:
        pass
