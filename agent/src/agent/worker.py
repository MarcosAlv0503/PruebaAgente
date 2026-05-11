"""Worker loop that pulls work units from the ``queue`` table.

v0.1.0 stub: connects, polls every ``WORKER_POLL_INTERVAL_S`` seconds (default
5), logs ``no work`` when the queue is empty, and exits cleanly on SIGINT.

Real projects replace ``_handle_execution`` with the LangGraph driver from
``agent.graph`` and add idempotency / retry policy as needed.
"""

from __future__ import annotations

import os
import signal
import time
from types import FrameType

import psycopg

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
    """Reserve the oldest unlocked queue entry for this worker.

    Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` so multiple workers can run
    side by side without colliding.
    """
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
    """Process one execution.

    The v0.1.x template stub does not run any real work; it only closes the
    execution lifecycle so ``make rn`` does not leave rows stuck in
    ``running`` or queue entries pending. The consuming project replaces
    this body with a call to ``agent.graph.run(state)`` and richer status
    transitions.

    .. note::
       TODO loang-template: replace this stub with the real LangGraph
       invocation from ``agent.graph`` and project-specific status
       handling.
    """
    dsn = os.environ.get("DATABASE_URL")
    if dsn is None:
        _LOGGER.warning(
            "claimed execution=%s but DATABASE_URL unset; cannot close lifecycle",
            execution_id,
        )
        return
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE executions
            SET status = 'succeeded',
                output = %s::jsonb,
                started_at = COALESCE(started_at, now()),
                finished_at = now()
            WHERE id = %s
            """,
            ('{"stub": true}', execution_id),
        )
        cur.execute("DELETE FROM queue WHERE execution_id = %s", (execution_id,))
        conn.commit()
    _LOGGER.info(
        "claimed execution=%s closed as succeeded (template stub — no work performed)",
        execution_id,
    )


if __name__ == "__main__":
    main()
