"""Phase 1 — deterministic: validate input, check idempotency, extract keywords."""
from __future__ import annotations

import re
from typing import Any

from agent._logging import get_logger
from agent.tools.check_duplicate import check_duplicate
from agent.tools.get_customer_context import get_customer_context

_LOGGER = get_logger("phase.intake")
_PHASE = "deterministic"

# Ordered from most specific to most general; first match wins.
# "critical" is reserved for systemic outages affecting ALL users.
# Individual user issues (my card, my order, I can't login) are "high".
_SEVERITY_RULES: list[tuple[list[str], str]] = [
    (["error 500", "web caída", "web caida", "no carga nada", "caído", "caido", "página no carga"], "critical"),
    (["checkout", "pagar", "pago", "tarjeta", "pedido", "compra", "no puedo pagar", "no deja pagar"], "high"),
    (["no puedo acceder", "login", "iniciar sesión", "iniciar sesion", "no puedo entrar"], "high"),
    (["imagen", "foto", "fotos", "no carga", "no cargan"], "high"),
    (["cupón", "cupon", "descuento", "código", "codigo", "promoción", "promocion"], "medium"),
    (["lento", "tarda", "va mal", "lentitud", "carga lenta"], "medium"),
    (["descripción", "descripcion", "precio", "stock"], "low"),
]

_TYPE_RULES: list[tuple[list[str], str]] = [
    (["checkout", "pagar", "pago", "tarjeta", "pedido", "compra", "pasarela"], "payment"),
    (["login", "iniciar sesión", "iniciar sesion", "contraseña", "contrasena", "acceder", "sesión", "sesion", "cuenta"], "access"),
    (["imagen", "foto", "descripción", "descripcion", "precio", "stock", "contenido"], "content"),
    (["cupón", "cupon", "descuento", "código", "codigo", "filtro", "carrito", "promoción"], "functional"),
    (["error", "lento", "carga", "caída", "caida", "500", "falla", "fallo", "lentitud"], "technical"),
]

_STOP_WORDS: frozenset[str] = frozenset({
    "el", "la", "los", "las", "un", "una", "de", "que", "en", "y", "no", "se",
    "por", "con", "para", "al", "del", "es", "a", "le", "su", "me", "mi", "te",
    "nos", "hay", "ya", "si", "más", "mas", "pero", "como", "bien", "muy",
})


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Validate input, check idempotency, extract keywords, apply heuristic classification.

    This phase is deterministic: no LLM, pure code. Cost: zero.
    On duplicate detection, sets is_duplicate=True and returns early — no further phases run.
    """
    _LOGGER.info("[phase.intake] execution=%s", state.get("execution_id"))

    message: str = str(state.get("incident_message", "")).strip()
    if not message:
        raise ValueError("incident_message is empty")
    if len(message) > 2000:
        raise ValueError(f"incident_message too long ({len(message)} chars, max 2000)")

    customer_id: str = str(state["customer_id"])
    external_id: str | None = state["input"].get("external_id")
    execution_id: str = str(state["execution_id"])

    is_dup = check_duplicate(_PHASE, customer_id, external_id, execution_id)
    state["is_duplicate"] = is_dup
    if is_dup:
        _LOGGER.info("[phase.intake] duplicate detected external_id=%s — skipping", external_id)
        return state

    state["customer_context"] = get_customer_context(_PHASE, customer_id)
    state["extracted_keywords"] = _extract_keywords(message)
    state["initial_severity"] = _classify_severity(message)
    state["initial_category"] = _classify_type(message)

    _LOGGER.info(
        "[phase.intake] execution=%s keywords=%s severity=%s category=%s",
        execution_id,
        state["extracted_keywords"],
        state["initial_severity"],
        state["initial_category"],
    )
    return state


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"\b\w{3,}\b", text.lower())
    return [w for w in dict.fromkeys(words) if w not in _STOP_WORDS][:12]


def _classify_severity(text: str) -> str | None:
    lower = text.lower()
    for keywords, severity in _SEVERITY_RULES:
        if any(kw in lower for kw in keywords):
            return severity
    return None


def _classify_type(text: str) -> str | None:
    lower = text.lower()
    for keywords, type_ in _TYPE_RULES:
        if any(kw in lower for kw in keywords):
            return type_
    return None
