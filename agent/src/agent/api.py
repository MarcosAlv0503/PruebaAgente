"""FastAPI app exposing the agent's HTTP surface.

The v0.1.0 template only wires ``/health`` so docker-compose, Fly.io and the
dashboard can probe the service. Project-specific endpoints are added under
``/api/...`` by replacing the stubs here.
"""

from __future__ import annotations

import os
from typing import Final

import psycopg
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict

_LOGGER_COMPONENT: Final[str] = "api"

app = FastAPI(
    title="Loang Template Agent API",
    description="Skeleton FastAPI app for the Loang IA template-agent.",
    version="0.1.0",
)


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    db: str


@app.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    """Liveness + DB readiness probe.

    Returns ``status="ok"`` when the FastAPI process is up. ``db="ok"`` only
    when a one-shot ``SELECT 1`` succeeds; ``db="unreachable"`` otherwise.
    """
    db_status = _probe_database()
    return HealthStatus(status="ok", db=db_status)


@app.post("/api/executions/{execution_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_execution(execution_id: str) -> dict[str, str]:
    """Cancel a running execution.

    .. note::
       TODO loang-template: implement cancellation against ``executions`` and
       ``queue`` tables. Replace this stub before going live.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="cancel_execution is a template stub; project must implement it",
    )


@app.post("/api/issues/{issue_id}/resolve", status_code=status.HTTP_202_ACCEPTED)
def resolve_issue(issue_id: str) -> dict[str, str]:
    """Mark a human-flagged issue as resolved.

    .. note::
       TODO loang-template: implement once the ``issues`` table lands in v0.2.0.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="resolve_issue is a template stub; project must implement it",
    )


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
