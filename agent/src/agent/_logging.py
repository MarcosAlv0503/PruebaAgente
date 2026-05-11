"""JSON-structured logging helper for the agent.

Mirrors the format used by ``loang_toolkit._logging`` so operators can grep
across both with the same tooling. Emits one JSON object per record to
stdout via a single handler attached to the ``agent`` logger. ``propagate``
is intentionally left at the default (``True``) so pytest ``caplog`` and
other downstream handlers still see the records.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, Final

_LOGGER_ROOT: Final[str] = "agent"
_RESERVED_LOGRECORD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)

_configured: bool = False


class _JsonFormatter(logging.Formatter):
    """Render :class:`logging.LogRecord` instances as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        component = record.name.removeprefix(f"{_LOGGER_ROOT}.")
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "component": component,
            "message": f"[{component}] {record.getMessage()}",
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOGRECORD_KEYS:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _configure_root_logger() -> None:
    """Install the JSON handler on the ``agent`` logger exactly once."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger(_LOGGER_ROOT)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    _configured = True


def get_logger(component: str) -> logging.Logger:
    """Return a logger scoped to ``component``.

    Args:
        component: Short identifier used as the log name suffix and the
            ``[component]`` prefix in every emitted line. Must be a valid
            identifier (alphanumerics + underscore).

    Returns:
        A :class:`logging.Logger` named ``agent.<component>``.
    """
    if not component or not component.replace("_", "").isalnum():
        raise ValueError(f"Invalid component name: {component!r}")
    _configure_root_logger()
    return logging.getLogger(f"{_LOGGER_ROOT}.{component}")
