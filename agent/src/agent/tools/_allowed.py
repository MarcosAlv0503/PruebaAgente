"""Tool whitelist by phase.

Each phase declares which tools it may invoke. The dispatcher (``agent.graph``)
checks ``tool_name in ALLOWED_TOOLS_BY_PHASE[phase]`` *before* calling the
tool, and the tool itself re-checks it as a defence-in-depth measure
(Playbook §5.1.2 — bloqueo en dos niveles).

# TODO loang-template: populate this map with the real tools per phase. The
# canonical phases are ``deterministic``, ``light_llm`` and ``heavy_llm``;
# rename to match the project's actual pipeline.
"""

from __future__ import annotations

from typing import Final

ALLOWED_TOOLS_BY_PHASE: Final[dict[str, frozenset[str]]] = {
    "deterministic": frozenset(),
    "light_llm": frozenset(),
    "heavy_llm": frozenset(),
}


def is_tool_allowed(phase: str, tool_name: str) -> bool:
    """Return whether ``tool_name`` may be invoked in ``phase``."""
    return tool_name in ALLOWED_TOOLS_BY_PHASE.get(phase, frozenset())
