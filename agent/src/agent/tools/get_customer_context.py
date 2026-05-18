"""Tool: fetch customer metadata from the customers table."""
from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agent._logging import get_logger
from agent.tools._allowed import is_tool_allowed

_LOGGER = get_logger("tool.get_customer_context")


def get_customer_context(current_phase: str, customer_id: str) -> dict[str, Any]:
    """Return name and external_ref for the given customer_id.

    Defence-in-depth: validates its own phase permission before touching the DB.
    Returns a minimal fallback dict if the DB is unreachable or the row is not found.
    """
    if not is_tool_allowed(current_phase, "get_customer_context"):
        raise PermissionError(f"get_customer_context not allowed in phase '{current_phase}'")

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return {"customer_id": customer_id, "name": "unknown"}

    with psycopg.connect(dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id::text, name, external_ref FROM customers WHERE id = %s::uuid LIMIT 1",
            (customer_id,),
        )
        row = cur.fetchone()

    if row is None:
        _LOGGER.warning("[tool.get_customer_context] customer_id=%s not found", customer_id)
        return {"customer_id": customer_id, "name": "unknown"}

    return dict(row)
