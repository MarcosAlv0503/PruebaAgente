"""Thin Anthropic SDK wrapper used by agent phases."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
import yaml

from agent._logging import get_logger

_LOGGER = get_logger("services.llm_client")


@dataclass(frozen=True)
class Prompt:
    name: str
    model: str
    temperature: float
    max_tokens: int
    body: str


def load_prompt(path: Path) -> Prompt:
    """Parse YAML front-matter and body from a versioned prompt file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Prompt file has no YAML front-matter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed front-matter in: {path}")
    meta: dict[str, Any] = yaml.safe_load(parts[1])
    return Prompt(
        name=str(meta["name"]),
        model=str(meta["model"]),
        temperature=float(meta.get("temperature", 0.1)),
        max_tokens=int(meta.get("max_tokens", 800)),
        body=parts[2].strip(),
    )


def chat(
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    execution_id: str = "",
) -> str:
    """Call Anthropic API and return the text of the first content block."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable must be set")

    client = anthropic.Anthropic(api_key=api_key)
    _LOGGER.info(
        "[services.llm_client] model=%s max_tokens=%d execution=%s",
        model,
        max_tokens,
        execution_id,
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,  # type: ignore[arg-type]
    )

    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected content block type: {block.type}")
    return block.text  # type: ignore[union-attr]
