# `agent/` — convenciones

Backend del agente. Stack: Python 3.13, FastAPI, LangGraph, psycopg 3, Alembic, [`loang-toolkit`](https://github.com/LoangIA/loang-toolkit).

## Top 5 cosas que NO hacer

1. **No metas lógica de negocio en `api.py` ni en `worker.py`.** Esos son orquestadores. Todo lo que hace el agente vive en `phases/<NN>_<name>.py`. Consecuencia: imposible de testear por fase.
2. **No abras conexiones a Postgres ad-hoc.** Usa el pool de [`agent/src/agent/db.py`](src/agent/db.py) cuando exista. Hasta entonces (v0.1.0), pasa la conexión como argumento. Consecuencia: pool exhaustion.
3. **No llames a OpenRouter sin pasar por `loang_toolkit.OpenRouterClient`.** Tracking, retry y circuit breaker son obligatorios — el toolkit los centraliza. Consecuencia: pierdes telemetría y te puedes comer un run de coste runaway.
4. **No mezcles fases.** `phase_deterministic` no llama a LLM, `phase_light_llm` usa modelo barato (haiku/mini), `phase_heavy_llm` usa modelo caro. Cada una con su whitelist en `tools/_allowed.py`. Consecuencia: coste explota o calidad cae sin diagnóstico.
5. **No saltes el bloqueo de tools en dos niveles.** El dispatcher valida contra `ALLOWED_TOOLS_BY_PHASE` ANTES de invocar la tool, y la propia tool revalida. Consecuencia: una fase ligera puede acabar invocando tools caros sin querer.

## Convenciones

- Tipos: `mypy --strict`. Sin `Any` salvo justificado en docstring.
- Logs: JSON estructurados a stdout con `agent._logging.get_logger("<component>")`. Mismo formato que el del toolkit (`{timestamp, level, component, message}` con prefijo `[component]` en `message`); el toolkit usa el suyo para sus propios componentes y el agente usa el suyo para los del proyecto.
- Schemas pydantic: `model_config = ConfigDict(extra="forbid")`.
- Schemas JSON: `additionalProperties: false`.
- Idioma: inglés (variables, funciones, comentarios, schema BD, logs).

## Estructura

```
agent/
├── src/agent/
│   ├── api.py             ← FastAPI app (orquestador HTTP)
│   ├── worker.py          ← loop de la cola (orquestador async)
│   ├── cli.py              ← entradas humanas (`make rn`, `make rn-retry`)
│   ├── graph.py            ← LangGraph stub con tres fases
│   ├── phases/             ← lógica del agente por fase
│   ├── tools/              ← whitelist por fase + dispatcher
│   ├── services/clients/   ← clientes a sistemas externos del cliente final
│   ├── prompts/            ← versionados con front-matter
│   ├── schemas/            ← input/output JSON schemas
│   ├── examples/           ← casos canónicos
│   ├── context/            ← misión y criterio del agente
│   └── roadmap/            ← decisiones pendientes y changelog del agente
├── alembic/                ← migraciones
└── tests/                  ← unit + smoke
```

## Cómo añadir una fase nueva

1. Documenta la decisión en `agent/src/agent/roadmap/decisiones-pendientes.md` (etiquéta D-N).
2. Crea `agent/src/agent/phases/NN_<nombre>.py` con función pura `(state) -> state`.
3. Añade tools permitidos en `agent/src/agent/tools/_allowed.py`.
4. Cablea la fase en `agent/src/agent/graph.py`.
5. Test de comportamiento en `agent/tests/test_phase_<nombre>.py`.
6. Anota en `agent/src/agent/roadmap/changelog.md`.
