"""Tool: fetch recent succeeded executions for a customer."""
from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agent._logging import get_logger
from agent.tools._allowed import is_tool_allowed

_LOGGER = get_logger("tool.get_recent_incidents")


def get_recent_incidents(
    current_phase: str,
    customer_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return the most recent succeeded executions for this customer.

    Useful for providing context to the LLM about recurring or related incidents.
    Defence-in-depth: validates its own phase permission before touching the DB.
    """
    if not is_tool_allowed(current_phase, "get_recent_incidents"):
        raise PermissionError(f"get_recent_incidents not allowed in phase '{current_phase}'")

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return []

    with psycopg.connect(dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id::text, output, finished_at
            FROM executions
            WHERE customer_id = %s::uuid
              AND status = 'succeeded'
            ORDER BY finished_at DESC
            LIMIT %s
            """,
            (customer_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]
