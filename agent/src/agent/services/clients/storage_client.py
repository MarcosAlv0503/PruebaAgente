"""Storage client: write incident logs and escalation tickets to /Documentos/.

All writes from write_log and create_ticket tools must go through this module.
In v0.2.0, this will be replaced/complemented by Postgres (audit_log + issues tables).

Note: /Documentos/ is not persistent on Fly.io between deploys (accepted tradeoff for v0.1.x).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agent._logging import get_logger

_LOGGER = get_logger("storage_client")

_DOCS_ROOT = Path(os.environ.get("DOCS_PATH", "/Documentos"))
_LOGS_DIR = _DOCS_ROOT / "logs"
_TICKETS_DIR = _DOCS_ROOT / "tickets"


def write_log(
    *,
    incident_id: str,
    execution_id: str,
    reporter: str,
    channel: str,
    incident_type: str,
    severity: str,
    confidence: float,
    auto_resolved: bool,
    message: str,
    response: str,
    kb_refs: list[str],
) -> str:
    """Write a structured incident log to /Documentos/logs/. Returns the absolute file path."""
    _ensure_dir(_LOGS_DIR)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}_{incident_id}_{incident_type}.txt"
    path = _LOGS_DIR / filename
    timestamp = datetime.now(timezone.utc).isoformat()
    kb_refs_str = "\n              ".join(kb_refs) if kb_refs else "none"

    content = (
        "INCIDENT LOG\n"
        "============\n"
        f"incident_id:    {incident_id}\n"
        f"execution_id:   {execution_id}\n"
        f"timestamp:      {timestamp}\n"
        f"reporter:       {reporter}\n"
        f"channel:        {channel}\n"
        f"type:           {incident_type}\n"
        f"severity:       {severity}\n"
        f"confidence:     {confidence:.3f}\n"
        f"auto_resolved:  {str(auto_resolved).lower()}\n"
        f"message:        {message}\n"
        f"response:       {response}\n"
        f"kb_refs:        {kb_refs_str}\n"
    )

    path.write_text(content, encoding="utf-8")
    _LOGGER.info("[storage_client] log written path=%s", path)
    return str(path)


def write_ticket(
    *,
    execution_id: str,
    priority: str,
    summary: str,
    reporter: str,
    incident_message: str,
    context: str,
    escalation_reason: str,
    suggested_steps: str,
) -> str:
    """Write a structured escalation ticket to /Documentos/tickets/. Returns the absolute file path."""
    _ensure_dir(_TICKETS_DIR)

    ticket_id = str(uuid.uuid4())
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}_{ticket_id}_{priority}.txt"
    path = _TICKETS_DIR / filename
    timestamp = datetime.now(timezone.utc).isoformat()

    content = (
        "INCIDENT TICKET\n"
        "===============\n"
        f"ticket_id:          {ticket_id}\n"
        f"execution_id:       {execution_id}\n"
        f"timestamp:          {timestamp}\n"
        f"priority:           {priority}\n"
        f"summary:            {summary}\n"
        f"reporter:           {reporter}\n"
        f"incident_message:   {incident_message}\n"
        f"context:            {context}\n"
        f"escalation_reason:  {escalation_reason}\n"
        f"suggested_steps:    {suggested_steps}\n"
    )

    path.write_text(content, encoding="utf-8")
    _LOGGER.info("[storage_client] ticket written path=%s", path)
    return str(path)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
