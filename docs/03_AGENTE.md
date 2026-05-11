# Agente — convenciones y cómo extender

## Las tres fases canónicas

El agente sigue siempre la misma secuencia (playbook §5.1, multi-modelo por fase):

1. **`phase_deterministic`** — código puro. Validaciones, lookups, transformaciones determinísticas. Coste cero.
2. **`phase_light_llm`** — modelo barato (gpt-4o-mini, haiku). La mayoría de las ejecuciones acaba aquí.
3. **`phase_heavy_llm`** — modelo grande (sonnet, gpt-4.1). Solo cuando la fase ligera no resuelve.

El driver vive en [`agent/src/agent/graph.py`](../agent/src/agent/graph.py). v0.1.0 lleva las tres como stubs.

## Cómo añadir una fase

1. **ADR.** Documenta la decisión en `docs/00_DECISIONES.md` o, si la decisión es del agente y no de toda la arquitectura, en [`agent/src/agent/roadmap/decisiones-pendientes.md`](../agent/src/agent/roadmap/decisiones-pendientes.md).
2. **Crea el módulo.** `agent/src/agent/phases/NN_<nombre>.py` con función pura `(state) -> state`. `NN` es orden de ejecución.
3. **Whitelist de tools.** Añade entrada en [`agent/src/agent/tools/_allowed.py`](../agent/src/agent/tools/_allowed.py).
4. **Cablea en el grafo.** Importa la fase en `graph.py` y enchúfala al routing.
5. **Test de comportamiento.** `agent/tests/test_phase_<nombre>.py` con al menos un caso golden. Cobertura ≥70%.
6. **Anota.** Una línea en [`agent/src/agent/roadmap/changelog.md`](../agent/src/agent/roadmap/changelog.md).

## Cómo añadir una tool

1. **ADR breve** en `roadmap/decisiones-pendientes.md` si la tool toca un sistema externo que no estaba antes.
2. **Implementa.** `agent/src/agent/tools/<nombre>.py` con docstring que describa qué hace y qué efectos secundarios tiene.
3. **Whitelist.** Añade el nombre a `ALLOWED_TOOLS_BY_PHASE[<fase>]` en `_allowed.py`.
4. **Defence-in-depth.** La propia tool, antes de actuar, valida `is_tool_allowed(current_phase, tool_name)`. Sin eso, una fase ligera podría invocarla saltándose el dispatcher.
5. **Test.** Mocking del sistema externo, no integración real (eso va en `tests/integration/`, fuera del CI obligatorio).

## Versionado de prompts

Convención de archivo: [`agent/src/agent/prompts/<role>-v<n>-<YYYY-MM-DD>.md`](../agent/src/agent/prompts/).

Front-matter YAML obligatorio (validado por `loang_toolkit.PromptLoader` con Pydantic strict, `extra="forbid"`):

```yaml
name: <nombre lógico del prompt>
model: <modelo OpenRouter>
temperature: <float>
max_tokens: <int>
version: "<número o etiqueta>"
output_format: <"text" | "json" | "markdown" | ...>
```

Cuando bumpeas un prompt:

1. Crea archivo nuevo con `<role>-v<n+1>-<YYYY-MM-DD>.md`.
2. Mantén el archivo viejo por al menos un release; permite rollback rápido.
3. Cambia la fase para apuntar al nuevo (mismo `name`, `version` distinto).
4. `agent_usage.prompt_version` registra qué versión generó cada ejecución — cruza coste/calidad antes de retirar la versión vieja.

## Token tracking

`loang_toolkit.OpenRouterClient(tracker=TokenTracker(conn), ...)`. Cada `chat()`/`achat()` con `execution_id` persiste en `agent_usage`. Con `prompt_version` correlacionas coste por iteración del prompt.

## Circuit breaker

`OpenRouterClient(max_tokens_per_run=...)`. Pre-call: rechaza si `used + max_tokens > limit`. Post-call: persiste primero en `agent_usage`, luego levanta `CircuitBreakerError`. Resultado: ningún run runaway pierde telemetría.

## Idempotencia

`executions` tiene `UNIQUE(customer_id, external_id)`. Si el upstream reintenta con el mismo `external_id`, el INSERT falla con conflicto y el worker no ejecuta dos veces. v0.1.0 no implementa el manejo del conflicto en `cli.py` — TODO `loang-template:` añadirlo si el proyecto recibe webhooks reintetrables.
