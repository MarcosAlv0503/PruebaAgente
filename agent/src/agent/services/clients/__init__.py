"""External provider clients (single-centralised-client pattern).

Pattern: one module per external system, named ``services/clients/<provider>.py``.
Each module exposes a class whose surface mirrors the domain operation we use,
not the provider's full API.

# TODO loang-template: when the project adds its first integration, drop a
# file like ``services/clients/holded.py`` here with a class
# ``HoldedClient`` that takes config in the constructor and exposes only the
# methods the agent calls. Keep the OpenRouter integration in
# ``loang_toolkit.OpenRouterClient`` — do not duplicate it here.
"""

from __future__ import annotations

__all__: list[str] = []
