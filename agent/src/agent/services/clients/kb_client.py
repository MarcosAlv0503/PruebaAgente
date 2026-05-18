"""Knowledge base client: keyword search over agent/knowledge/*.md files.

MVP implementation: reads markdown files, scores by keyword frequency, returns top-K.
v0.2.0 target: replace with pgvector semantic search (ADR pending).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from agent._logging import get_logger

_LOGGER = get_logger("kb_client")


def _kb_root() -> Path:
    env = os.environ.get("KB_PATH")
    if env:
        return Path(env)
    # Resolve from this file's location:
    # services/clients/kb_client.py → parents[4] = package root (agent/)
    # knowledge/ lives at agent/knowledge/ alongside src/
    return Path(__file__).parents[4] / "knowledge"


def search(keywords: list[str], top_k: int = 3) -> list[dict[str, Any]]:
    """Search KB markdown files by keyword frequency. Returns up to top_k matches.

    Each result contains: path (relative), score (keyword hits), title, excerpt (first 600 chars).
    Files starting with '_' are skipped (reserved for deprecated docs).
    """
    if not keywords:
        return []

    root = _kb_root()
    if not root.exists():
        _LOGGER.warning("[kb_client] knowledge dir not found: %s", root)
        return []

    scored: list[tuple[int, Path]] = []
    for md_file in root.rglob("*.md"):
        if md_file.name.startswith("_"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        score = sum(
            len(re.findall(rf"\b{re.escape(kw.lower())}\b", content))
            for kw in keywords
        )
        if score > 0:
            scored.append((score, md_file))

    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[dict[str, Any]] = []
    for score, path in scored[:top_k]:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        results.append({
            "path": str(path.relative_to(root.parent)),
            "score": score,
            "title": _extract_title(raw),
            "excerpt": raw[:600].strip(),
        })

    return results


def _extract_title(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Sin título"
