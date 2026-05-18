"""Tool: write structured incident log to /Documentos/logs/."""
from __future__ import annotations

from agent.services.clients import storage_client
from agent.tools._allowed import is_tool_allowed


def write_log(
    current_phase: str,
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
    """Write a structured .txt log to /Documentos/logs/. Returns the file path.

    Defence-in-depth: validates its own phase permission before writing to disk.
    All writes go through storage_client — never write directly to /Documentos/.
    """
    if not is_tool_allowed(current_phase, "write_log"):
        raise PermissionError(f"write_log not allowed in phase '{current_phase}'")

    return storage_client.write_log(
        incident_id=incident_id,
        execution_id=execution_id,
        reporter=reporter,
        channel=channel,
        incident_type=incident_type,
        severity=severity,
        confidence=confidence,
        auto_resolved=auto_resolved,
        message=message,
        response=response,
        kb_refs=kb_refs,
    )
