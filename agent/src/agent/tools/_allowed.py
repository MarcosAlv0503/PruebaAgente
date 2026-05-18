"""Tool whitelist by phase.

Each phase declares which tools it may invoke. The dispatcher (``agent.graph``)
checks ``tool_name in ALLOWED_TOOLS_BY_PHASE[phase]`` *before* calling the
tool, and the tool itself re-checks it as a defence-in-depth measure
(Playbook §5.1.2 — bloqueo en dos niveles).

"""

from __future__ import annotations

from typing import Final

ALLOWED_TOOLS_BY_PHASE: Final[dict[str, frozenset[str]]] = {
    "deterministic": frozenset({
        "check_duplicate",
        "get_customer_context",
        "write_log",
    }),
    "light_llm": frozenset({
        "search_knowledge_base",
        "get_recent_incidents",
        "write_log",
    }),
    "heavy_llm": frozenset({
        "search_knowledge_base",
        "get_recent_incidents",
        "write_log",
        "create_ticket",
    }),
}


def is_tool_allowed(phase: str, tool_name: str) -> bool:
    """Return whether ``tool_name`` may be invoked in ``phase``."""
    return tool_name in ALLOWED_TOOLS_BY_PHASE.get(phase, frozenset())
