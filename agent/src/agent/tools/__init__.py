"""Agent tools and the per-phase whitelist.

The two-level blocking pattern (Playbook §5.1.2): the dispatcher validates the
tool call against ``ALLOWED_TOOLS_BY_PHASE`` *and* the tool implementation
revalidates. v0.1.0 ships an empty whitelist so projects must opt tools in
explicitly.
"""

from ._allowed import ALLOWED_TOOLS_BY_PHASE

__all__ = ["ALLOWED_TOOLS_BY_PHASE"]
