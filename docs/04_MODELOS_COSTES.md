# Modelos y costes

## Asignación de modelo por fase

| Fase | Modelo (OpenRouter) | Rol | Coste aproximado / 1K tokens |
|---|---|---|---|
| `phase_deterministic` | Sin LLM | Validación y extracción por código puro | $0 |
| `phase_light_llm` | `anthropic/claude-haiku-4-5` | Clasificación estructurada + KB lookup + respuesta | Input: ~$0.80 / Output: ~$4.00 |
| `phase_heavy_llm` | `anthropic/claude-sonnet-4-5` | Análisis profundo + generación de ticket | Input: ~$3.00 / Output: ~$15.00 |

> Precios aproximados en OpenRouter a 2026-05. Verificar en https://openrouter.ai/models antes de presupuestar.

## Estimación de coste por ejecución

**Escenario típico (resolución automática en phase_light_llm):**
- Tokens input: ~600 (prompt + mensaje + top-3 KB excerpts)
- Tokens output: ~300 (clasificación JSON + respuesta)
- Coste estimado: ~$0.002 por incidencia

**Escenario de escalación (light + heavy):**
- Phase light: ~$0.002
- Phase heavy: ~600 tokens input + 400 output → ~$0.008
- Coste estimado: ~$0.010 por incidencia

**Mix esperado (75% auto, 25% escala):**
- Coste medio por incidencia: ~$0.004

## Circuit breaker

Configurado en `loang_toolkit.OpenRouterClient`:

```
CIRCUIT_BREAKER_MAX_TOKENS=4000
```

- Pre-call: rechaza si `tokens_used + estimated_tokens > CIRCUIT_BREAKER_MAX_TOKENS`.
- Post-call: persiste en `agent_usage` primero, luego levanta `CircuitBreakerError`.
- Worker: captura `CircuitBreakerError` → `executions.status='failed'`, `error='budget_exceeded'`.

## Variables de entorno de modelos

```env
OPENROUTER_API_KEY=<clave>
CONFIDENCE_THRESHOLD=0.75
CIRCUIT_BREAKER_MAX_TOKENS=4000
MODEL_LIGHT=anthropic/claude-haiku-4-5
MODEL_HEAVY=anthropic/claude-sonnet-4-5
```

## Token tracking

`loang_toolkit.TokenTracker(conn)` persiste en `agent_usage`:

| Campo | Contenido |
|---|---|
| `execution_id` | FK a `executions` |
| `phase` | `light_llm` / `heavy_llm` |
| `model` | Modelo OpenRouter usado |
| `prompt_version` | Versión del prompt cargado |
| `tokens_input` | Tokens de prompt |
| `tokens_output` | Tokens de completion |
| `cost_usd` | Coste calculado por el cliente |

Con `prompt_version` se puede cruzar coste/calidad antes de retirar una versión de prompt.

## Estrategia de bumps de modelo

1. Cuando salga una versión nueva de haiku o sonnet en OpenRouter, abrir ADR en `docs/00_DECISIONES.md`.
2. Evaluar calidad sobre los casos golden de `agent/examples/` antes de bumpar.
3. Bumpar `MODEL_LIGHT` / `MODEL_HEAVY` en `.env.example` y en el ADR.
4. Mantener el prompt anterior activo al menos un release para permitir rollback rápido.
