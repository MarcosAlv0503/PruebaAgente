"""LangGraph stub with three placeholder phases.

The v0.1.0 template defines the canonical three-phase shape so that every
project clone follows the same pattern (Playbook §5.1, multi-modelo por fase):

- ``phase_deterministic`` — no LLM, pure code (validations, lookups).
- ``phase_light_llm`` — small/cheap model (haiku, gpt-4o-mini class).
- ``phase_heavy_llm`` — bigger model only when light cannot finish the job.

Replace the function bodies with real logic when starting a new project. The
``State`` type and the graph wiring stay; the contents change.
"""

from __future__ import annotations

from typing import Any, TypedDict

from agent._logging import get_logger

_LOGGER = get_logger("graph")


class State(TypedDict):
    """Mutable state threaded through the graph.

    Replace the optional fields with project-specific ones; keep ``execution_id``
    and ``customer_id`` so token tracking and audit logs stay coherent.
    """

    execution_id: str
    customer_id: str
    input: dict[str, Any]
    summary: str | None
    light_output: dict[str, Any] | None
    heavy_output: dict[str, Any] | None


def phase_deterministic(state: State) -> State:
    """Pure code phase. Validate the input, fetch precomputed data, etc.

    .. note::
       TODO loang-template: replace with the project's validation /
       pre-processing logic.
    """
    _LOGGER.info("[graph] phase_deterministic execution=%s", state["execution_id"])
    state["summary"] = "deterministic-stub"
    return state


def phase_light_llm(state: State) -> State:
    """Light LLM phase. Use a cheap model via ``loang_toolkit.OpenRouterClient``.

    .. note::
       TODO loang-template: instantiate ``OpenRouterClient`` from
       ``loang_toolkit`` here, load a prompt with ``PromptLoader`` and
       record usage with ``TokenTracker``.
    """
    _LOGGER.info("[graph] phase_light_llm execution=%s", state["execution_id"])
    state["light_output"] = {"stub": True}
    return state


def phase_heavy_llm(state: State) -> State:
    """Heavy LLM phase. Only invoked when the light phase cannot finish.

    .. note::
       TODO loang-template: implement the gating that decides whether to call
       the heavy model based on ``state["light_output"]``.
    """
    _LOGGER.info("[graph] phase_heavy_llm execution=%s", state["execution_id"])
    state["heavy_output"] = {"stub": True}
    return state


def build_summary(state: State) -> str:
    """Concatenate the per-phase outputs into a stable summary string.

    Used between phases and at the end for ``audit_log`` / ``executions.output``.
    """
    pieces: list[str] = []
    if state.get("summary"):
        pieces.append(f"summary={state['summary']}")
    if state.get("light_output") is not None:
        pieces.append(f"light={state['light_output']!r}")
    if state.get("heavy_output") is not None:
        pieces.append(f"heavy={state['heavy_output']!r}")
    return " | ".join(pieces) or "(empty)"


def run(state: State) -> State:
    """Run the three phases sequentially. Replace with a real LangGraph
    ``StateGraph`` once phases need conditional routing.
    """
    state = phase_deterministic(state)
    state = phase_light_llm(state)
    if state.get("light_output", {}).get("needs_heavy"):  # type: ignore[union-attr]
        state = phase_heavy_llm(state)
    return state
