"""Command-line entry points used by ``make rn`` / ``make rn-retry``.

Usage::

    python -m agent.cli run --customer <customer-id>
    python -m agent.cli retry --execution <execution-id>

The v0.1.0 template wires creation of an ``executions`` row and an entry in
``queue``; the worker picks it up. Real project logic (validation, payload
shaping, observability) goes in ``phases/`` and is invoked via ``agent.graph``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Final

import psycopg

from agent._logging import get_logger

_LOGGER = get_logger("cli")

_COMPONENT: Final[str] = "cli"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Create a new execution and enqueue it")
    run.add_argument("--customer", required=True, help="UUID of an existing customer row")
    run.add_argument("--external-id", default=None, help="Idempotency key from upstream system")
    run.add_argument(
        "--input",
        default="{}",
        help="JSON-encoded input payload (default: empty object)",
    )

    retry = sub.add_parser("retry", help="Re-enqueue a failed execution")
    retry.add_argument("--execution", required=True, help="UUID of the execution to retry")

    args = parser.parse_args(argv)

    # Validate inputs that don't need a connection before opening one, so
    # bad arguments fail loud without touching the database.
    payload: dict[str, object] | None = None
    if args.command == "run":
        payload = _parse_json(args.input)

    dsn = _require_database_url()

    with psycopg.connect(dsn) as conn:
        if args.command == "run":
            assert payload is not None
            execution_id = _create_execution(
                conn,
                customer_id=args.customer,
                external_id=args.external_id,
                input_payload=payload,
            )
            _enqueue(conn, execution_id)
            _LOGGER.info(
                "[%s] enqueued execution=%s customer=%s",
                _COMPONENT,
                execution_id,
                args.customer,
            )
            print(execution_id)
            return 0
        _enqueue(conn, args.execution)
        _LOGGER.info("[%s] re-enqueued execution=%s", _COMPONENT, args.execution)
        return 0


def _require_database_url() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL must be set to use the CLI")
    return dsn


def _parse_json(raw: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--input must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("--input must decode to a JSON object")
    return parsed


def _create_execution(
    conn: psycopg.Connection[tuple[object, ...]],
    *,
    customer_id: str,
    external_id: str | None,
    input_payload: dict[str, object],
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO executions (customer_id, external_id, status, input)
            VALUES (%s, %s, 'pending', %s::jsonb)
            RETURNING id
            """,
            (customer_id, external_id, json.dumps(input_payload)),
        )
        row = cur.fetchone()
    conn.commit()
    if row is None:
        raise RuntimeError("INSERT INTO executions did not return an id")
    return str(row[0])


def _enqueue(conn: psycopg.Connection[tuple[object, ...]], execution_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO queue (execution_id) VALUES (%s)", (execution_id,))
    conn.commit()


if __name__ == "__main__":
    sys.exit(main())
