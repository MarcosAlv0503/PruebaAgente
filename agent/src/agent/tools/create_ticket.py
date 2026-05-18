"""Tool: write escalation ticket to /Documentos/tickets/."""
from __future__ import annotations

from agent.services.clients import storage_client
from agent.tools._allowed import is_tool_allowed


def create_ticket(
    current_phase: str,
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
    """Write a structured .txt ticket to /Documentos/tickets/. Returns the file path.

    Defence-in-depth: validates its own phase permission before writing to disk.
    All writes go through storage_client — never write directly to /Documentos/.
    """
    if not is_tool_allowed(current_phase, "create_ticket"):
        raise PermissionError(f"create_ticket not allowed in phase '{current_phase}'")

    return storage_client.write_ticket(
        execution_id=execution_id,
        priority=priority,
        summary=summary,
        reporter=reporter,
        incident_message=incident_message,
        context=context,
        escalation_reason=escalation_reason,
        suggested_steps=suggested_steps,
    )
