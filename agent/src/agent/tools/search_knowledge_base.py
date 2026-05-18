"""Tool: search the knowledge base by keyword."""
from __future__ import annotations

from typing import Any

from agent._logging import get_logger
from agent.services.clients.kb_client import search as kb_search
from agent.tools._allowed import is_tool_allowed

_LOGGER = get_logger("tool.search_knowledge_base")


def search_knowledge_base(
    current_phase: str,
    keywords: list[str],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Search agent/knowledge/*.md files by keyword frequency. Returns top_k matches.

    Defence-in-depth: validates its own phase permission before touching the filesystem.
    """
    if not is_tool_allowed(current_phase, "search_knowledge_base"):
        raise PermissionError(f"search_knowledge_base not allowed in phase '{current_phase}'")

    results = kb_search(keywords, top_k=top_k)
    _LOGGER.info(
        "[tool.search_knowledge_base] phase=%s keywords=%s found=%d",
        current_phase,
        keywords,
        len(results),
    )
    return results
