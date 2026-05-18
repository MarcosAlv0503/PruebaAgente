"""FastAPI app exposing the agent's HTTP surface."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from agent._logging import get_logger

_LOGGER = get_logger("api")

app = FastAPI(
    title="Loang Ecommerce Support Agent API",
    description="Backend API for the ecommerce incident support agent.",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    db: str


class ConversationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    customer_id: uuid.UUID
    external_id: str = Field(min_length=1)
    reported_at: datetime
    reporter: str = Field(min_length=1)
    channel: Literal["web"]
    # Multi-turn conversation fields (optional — omit for first message)
    thread_id: uuid.UUID | None = None
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=10)


class ExecutionQueued(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: str
    thread_id: str
    status: str


class ExecutionStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: str
    status: str
    output: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    finished_at: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    """Liveness + DB readiness probe."""
    db_status = _probe_database()
    return HealthStatus(status="ok", db=db_status)


@app.post("/api/incidents", status_code=status.HTTP_202_ACCEPTED, response_model=ExecutionQueued)
def create_incident(body: IncidentCreate) -> ExecutionQueued:
    """Submit a new incident for async processing.

    Creates an execution row (status=pending) and enqueues it for the worker.
    Idempotent: if (customer_id, external_id) already exists, returns the
    existing execution_id without re-queuing.

    Pass thread_id and conversation_history to maintain multi-turn context
    across consecutive messages in the same chat session.
    """
    dsn = _require_database_url()
    thread_id = body.thread_id or uuid.uuid4()
    with psycopg.connect(dsn) as conn:
        execution_id = _create_execution(conn, body, thread_id)
    _LOGGER.info(
        "[api] incident queued execution_id=%s customer_id=%s thread_id=%s",
        execution_id,
        body.customer_id,
        thread_id,
    )
    return ExecutionQueued(execution_id=execution_id, thread_id=str(thread_id), status="pending")


@app.get("/api/incidents/{execution_id}", response_model=ExecutionStatus)
def get_incident_status(execution_id: str) -> ExecutionStatus:
    """Return status and output of a previously submitted incident."""
    dsn = _require_database_url()
    try:
        with psycopg.connect(dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id::text, status, output, error,
                           created_at::text, finished_at::text
                    FROM executions
                    WHERE id = %s::uuid
                    """,
                    (execution_id,),
                )
                row = cur.fetchone()
    except psycopg.errors.InvalidTextRepresentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="execution not found",
        )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="execution not found",
        )

    return ExecutionStatus(
        execution_id=str(row["id"]),
        status=str(row["status"]),
        output=row["output"],
        error=row["error"],
        created_at=str(row["created_at"]),
        finished_at=str(row["finished_at"]) if row["finished_at"] else None,
    )


@app.post("/api/executions/{execution_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_execution(execution_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="cancel_execution not yet implemented",
    )


@app.post("/api/issues/{issue_id}/resolve", status_code=status.HTTP_202_ACCEPTED)
def resolve_issue(issue_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="resolve_issue not yet implemented",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_database_url() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured",
        )
    return dsn


def _create_execution(
    conn: psycopg.Connection[tuple[object, ...]],
    body: IncidentCreate,
    thread_id: uuid.UUID,
) -> str:
    """Insert execution + queue entry. Returns execution_id."""
    input_payload: dict[str, Any] = {
        "message": body.message,
        "customer_id": str(body.customer_id),
        "external_id": body.external_id,
        "reported_at": body.reported_at.isoformat(),
        "reporter": body.reporter,
        "channel": body.channel,
        "thread_id": str(thread_id),
        "conversation_history": [t.model_dump() for t in body.conversation_history],
    }
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO executions (customer_id, external_id, status, input, thread_id)
            VALUES (%s::uuid, %s, 'pending', %s::jsonb, %s::uuid)
            ON CONFLICT (customer_id, external_id) DO NOTHING
            RETURNING id::text
            """,
            (str(body.customer_id), body.external_id, json.dumps(input_payload), str(thread_id)),
        )
        row = cur.fetchone()

    if row is not None:
        execution_id = str(row[0])
        with conn.cursor() as cur:
            cur.execute("INSERT INTO queue (execution_id) VALUES (%s::uuid)", (execution_id,))
        conn.commit()
        return execution_id

    # Conflict: execution already exists — return its id without re-queuing
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id::text FROM executions WHERE customer_id = %s::uuid AND external_id = %s",
            (str(body.customer_id), body.external_id),
        )
        existing = cur.fetchone()
    conn.commit()
    if existing is None:
        raise RuntimeError("execution conflict but refetch returned nothing")
    return str(existing[0])


def _probe_database() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return "unconfigured"
    try:
        with psycopg.connect(dsn, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return "ok"
    except psycopg.Error:
        return "unreachable"
