"""Placeholder phase shipped with the template.

# TODO loang-template: delete this file and replace it with phase modules
# named ``00_<name>.py``, ``01_<name>.py``, ... matching the project's actual
# pipeline. Each function is pure: ``(state) -> state``.
"""

from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    """No-op placeholder kept so the package imports cleanly until a real
    phase is added.
    """
    return state
