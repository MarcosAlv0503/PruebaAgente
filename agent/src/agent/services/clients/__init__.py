"""External provider clients (single-centralised-client pattern).

Current clients:
- kb_client.py       — read-only search over agent/knowledge/*.md
- storage_client.py  — write logs and tickets to /Documentos/

Pattern: one module per external system. Each exposes only the operations the agent uses.
OpenRouter stays in loang_toolkit.OpenRouterClient — not duplicated here.
"""

from __future__ import annotations

__all__: list[str] = []
