"""Worker loop: claim executions from queue, run the agent graph, persist output."""
from __future__ import annotations

import json
import os
import signal
import time
from types import FrameType
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agent import graph
from agent._logging import get_logger

_LOGGER = get_logger("worker")
_DEFAULT_POLL_INTERVAL_S: float = 5.0
_LOCK_OWNER: str = os.environ.get("WORKER_NAME", "worker-default")
_running = True


def _handle_sigterm(_signum: int, _frame: FrameType | None) -> None:
    global _running
    _running = False
    _LOGGER.info("[worker] received shutdown signal")


def main() -> None:
    """Entry point. Run with ``python -m agent.worker``."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL must be set to run the worker")
    poll_interval = float(os.environ.get("WORKER_POLL_INTERVAL_S", _DEFAULT_POLL_INTERVAL_S))

    signal.signal(signal.SIGINT, _handle_sigterm)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    with psycopg.connect(dsn) as conn:
        _LOGGER.info("[worker] started owner=%s poll=%.1fs", _LOCK_OWNER, poll_interval)
        while _running:
            execution_id = _claim_one(conn)
            if execution_id is None:
                _LOGGER.info("[worker] no work")
                time.sleep(poll_interval)
                continue
            try:
                _handle_execution(execution_id)
            except Exception:
                _LOGGER.exception("[worker] execution=%s failed", execution_id)
        _LOGGER.info("[worker] stopped cleanly")


def _claim_one(conn: psycopg.Connection[tuple[object, ...]]) -> str | None:
    """Reserve the oldest unlocked queue entry with SELECT FOR UPDATE SKIP LOCKED."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE queue
            SET locked_at = now(), locked_by = %s, attempts = attempts + 1
            WHERE id = (
                SELECT id FROM queue
                WHERE locked_at IS NULL
                ORDER BY enqueued_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING execution_id
            """,
            (_LOCK_OWNER,),
        )
        row = cur.fetchone()
    conn.commit()
    if row is None:
        return None
    return str(row[0])


def _handle_execution(execution_id: str) -> None:
    """Load execution from DB, build State, run graph, persist output."""
    dsn = os.environ.get("DATABASE_URL")
    if dsn is None:
        _LOGGER.warning("[worker] DATABASE_URL unset, cannot handle execution=%s", execution_id)
        return

    with psycopg.connect(dsn) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id::text, customer_id::text, input FROM executions WHERE id = %s::uuid",
                (execution_id,),
            )
            row = cur.fetchone()

        if row is None:
            _LOGGER.error("[worker] execution=%s not found in DB", execution_id)
            return

        input_data: dict[str, Any] = dict(row["input"])

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE executions SET status='running', started_at=COALESCE(started_at, now()) WHERE id=%s::uuid",
                (execution_id,),
            )
        conn.commit()

    state: graph.State = {
        "execution_id": execution_id,
        "customer_id": str(row["customer_id"]),
        "input": input_data,
        "incident_message": str(input_data.get("message", "")),
        "reporter": str(input_data.get("reporter", "unknown")),
        "channel": str(input_data.get("channel", "web")),
        "reported_at": str(input_data.get("reported_at", "")),
        "summary": None,
        "light_output": None,
        "heavy_output": None,
        "is_duplicate": False,
        "customer_context": None,
        "extracted_keywords": [],
        "initial_category": None,
        "initial_severity": None,
        "classification": None,
        "kb_results": [],
        "proposed_response": None,
        "needs_heavy": False,
        "ticket": None,
        "escalation_reason": None,
        "thread_id": str(input_data.get("thread_id", "")),
        "conversation_history": [
            {"role": str(t["role"]), "content": str(t["content"])}
            for t in input_data.get("conversation_history", [])
            if isinstance(t, dict) and "role" in t and "content" in t
        ],
        "final_response": None,
        "log_ref": None,
        "ticket_ref": None,
    }

    with psycopg.connect(dsn) as conn:
        try:
            state = graph.run(state)
        except Exception as exc:
            _LOGGER.exception("[worker] execution=%s graph raised", execution_id)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE executions SET status='failed', error=%s, finished_at=now() WHERE id=%s::uuid",
                    (str(exc), execution_id),
                )
                cur.execute("DELETE FROM queue WHERE execution_id=%s::uuid", (execution_id,))
            conn.commit()
            return

        status = "failed" if state["is_duplicate"] else "succeeded"
        error: str | None = "duplicate_skipped" if state["is_duplicate"] else None

        output: dict[str, Any] = {
            "incident_id": execution_id,
            "auto_resolved": not state.get("needs_heavy", False),
            "classification": state.get("classification"),
            "final_response": state.get("final_response"),
            "kb_refs": [str(r.get("path", "")) for r in state.get("kb_results", [])],
            "ticket_ref": state.get("ticket_ref"),
            "log_ref": state.get("log_ref"),
        }

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE executions
                SET status=%s, output=%s::jsonb, error=%s, finished_at=now()
                WHERE id=%s::uuid
                """,
                (status, json.dumps(output), error, execution_id),
            )
            cur.execute("DELETE FROM queue WHERE execution_id=%s::uuid", (execution_id,))
        conn.commit()

    _LOGGER.info(
        "[worker] execution=%s status=%s auto_resolved=%s",
        execution_id,
        status,
        output["auto_resolved"],
    )


if __name__ == "__main__":
    main()
