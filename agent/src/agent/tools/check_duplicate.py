"""Tool: check if this external_id was already successfully processed."""
from __future__ import annotations

import os

import psycopg

from agent._logging import get_logger
from agent.tools._allowed import is_tool_allowed

_LOGGER = get_logger("tool.check_duplicate")


def check_duplicate(
    current_phase: str,
    customer_id: str,
    external_id: str | None,
    current_execution_id: str,
) -> bool:
    """Return True if a different execution with the same external_id already succeeded.

    Defence-in-depth: validates its own phase permission before querying the DB.
    Skips the check when external_id is None (manual CLI runs without idempotency key).
    """
    if not is_tool_allowed(current_phase, "check_duplicate"):
        raise PermissionError(f"check_duplicate not allowed in phase '{current_phase}'")

    if not external_id:
        return False

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        _LOGGER.warning("[tool.check_duplicate] DATABASE_URL not set, skipping check")
        return False

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM executions
            WHERE customer_id = %s::uuid
              AND external_id = %s
              AND id != %s::uuid
              AND status = 'succeeded'
            LIMIT 1
            """,
            (customer_id, external_id, current_execution_id),
        )
        return cur.fetchone() is not None
