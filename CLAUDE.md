# loang-ecommerce-support-agent

> Agente de soporte operativo para tiendas ecommerce de ropa. Clasifica incidencias técnicas y funcionales, resuelve automáticamente las documentadas en la KB y escala con trazabilidad completa las que requieren intervención humana.

## Estado actual

Sprint 0 completado — documentación, schemas y arquitectura definidos. Sprint 1 en curso: fases del agente.

## Top 6 cosas que NO hacer

1. **No ejecutes acciones sobre la plataforma ecommerce.** El agente analiza, clasifica y responde — nunca modifica la tienda ni ejecuta cambios en producción. Consecuencia: riesgo operativo directo sobre el negocio del cliente final.

2. **No respondas con confianza baja sin escalar.** Si `classification.confidence < CONFIDENCE_THRESHOLD` (env, default 0.75), la ejecución DEBE pasar a `phase_heavy_llm` o generar ticket. Consecuencia: el operador actúa sobre una respuesta incorrecta que aparenta ser autorizada por el agente.

3. **No inventes soluciones.** Las fases LLM solo responden con base en `agent/knowledge/`. Si la KB no tiene la respuesta, el agente escala. Sin excepciones. Consecuencia: instrucciones incorrectas con riesgo de daño operativo al cliente.

4. **No escribas en `agent/knowledge/` desde el código del agente.** La KB es estrictamente read-only para el agente. Las actualizaciones las hace el equipo humano via commit. Consecuencia: el agente contamina su propia fuente de verdad y las respuestas se vuelven inconsistentes.

5. **No mezcles responsabilidades entre fases.** `phase_deterministic` no llama a LLM; `phase_light_llm` no genera tickets ni escribe ficheros; `phase_heavy_llm` no valida el input. Consecuencia: coste impredecible, testing por fase imposible y routing erróneo.

6. **No writes a `/Documentos/` fuera de `storage_client`.** Todo fichero en `/Documentos/logs/` y `/Documentos/tickets/` pasa por `services/clients/storage_client.py`. Consecuencia: paths inconsistentes y pérdida silenciosa de trazabilidad operativa.

## Stack del proyecto

| Capa | Elección | Notas |
|---|---|---|
| Lenguaje del agente | Python 3.13 | |
| Orquestación LLM | LangGraph | |
| Pasarela de modelos | OpenRouter vía `loang-toolkit.OpenRouterClient` | |
| Fase light | `anthropic/claude-haiku-4-5` | Clasificación + KB lookup |
| Fase heavy | `anthropic/claude-sonnet-4-5` | Escalación + ticket |
| Backend HTTP | FastAPI | |
| BD | PostgreSQL | Postgres en Docker Compose local; Fly.io postgres en producción |
| Migraciones | Alembic | |
| Cliente Python a BD | psycopg 3 + queries preparadas | |
| Cliente TS a BD | `pg` (`node-postgres`) | |
| Tipos TS desde schema | Drizzle Kit `introspect` | |
| Frontend | Next.js 15 App Router + TypeScript | |
| UI | Tailwind + shadcn/ui | |
| Forms | react-hook-form + zod | |
| Tablas | TanStack Table | |
| Auth | NextAuth v5 estable | Deferido a v0.2.0 |
| Plataforma cloud | Fly.io | Región `mad` por defecto |
| Orquestación local | Docker Compose | Volume `/Documentos` montado |
| Observabilidad | Sentry (Python + Next) | Deferido a v0.2.0 |
| Logs | JSON estructurados a stdout | Formato `[component] message` |
| KB | Archivos `.md` en `agent/knowledge/` | Keyword search en v0.1.x; pgvector en v0.2.0 |
| Storage incidencias | Filesystem `/Documentos/` | Migración a Postgres en v0.2.0 |

(Desviaciones del estándar del playbook: ver `docs/00_DECISIONES.md`.)

## Convenciones no negociables

- Idioma del código: inglés (variables, funciones, comentarios, schema BD, logs, commits).
- Idioma de la UI del dashboard: español (operador hispanohablante).
- Idioma de la documentación (`docs/`, `CLAUDE.md`, prosa): español.
- Tipos: `mypy strict` en Python, `strict: true` en TS. Sin `any` ni `Any`.
- Logs: JSON estructurados a stdout, formato `[component] message`.
- Commits: `<type>: <description>` en inglés.

## Comandos esenciales

```bash
make up          # arranca todos los servicios (docker-compose)
make migrate     # aplica migraciones Alembic
make test        # tests + lint + types (Python + TS)
make rn ID=123   # procesa una incidencia concreta (customer_id)
```

## Mapa de documentación

Carga bajo demanda según en qué trabajes:

| Si trabajas en... | Carga `docs/...` |
|---|---|
| Decisiones arquitecturales | `00_DECISIONES.md` |
| Scope, capacidades, hitos del proyecto | `01_PROYECTO.md` |
| Arquitectura general | `02_ARQUITECTURA.md` |
| Lógica del agente | `03_AGENTE.md` + `agent/CLAUDE.md` |
| Modelos y costes | `04_MODELOS_COSTES.md` |
| Reglas de negocio del cliente | `05_DOMINIO.md` |
| Schema BD o queries | `06_BASE_DATOS.md` |
| Backend FastAPI | `07_BACKEND.md` |
| Frontend Next.js | `08_FRONTEND.md` + `dashboard/CLAUDE.md` |
| Operación / deploy | `09_OPERACION.md` + `RUNBOOK.md` |
| Anti-patrones extendidos | `10_ANTIPATRONES.md` |
| Seguridad | `SECURITY.md` |

## Coordinación entre devs

Si el proyecto trabaja con dos terminales Claude Code en paralelo (típico: uno en `agent/`, otro en `dashboard/`), copia `COORDINACION.md.template` a `COORDINACION.md` en raíz y mantenlo actualizado. El hook `UserPromptSubmit` configurado en `.claude/settings.json` lo inyecta automáticamente al contexto.

## Estructura del repo

```
loang-ecommerce-support-agent/
├── CLAUDE.md
├── README.md
├── docker-compose.yml                 ← volume /Documentos montado
├── .env.example
├── .gitignore
├── Makefile
├── .claude/
│   ├── settings.json
│   └── commands/
│       └── audit.md
├── docs/
│   ├── 00_DECISIONES.md
│   ├── 01_PROYECTO.md
│   ├── 02_ARQUITECTURA.md
│   ├── 03_AGENTE.md
│   ├── 04_MODELOS_COSTES.md
│   ├── 05_DOMINIO.md
│   ├── 06_BASE_DATOS.md
│   ├── 09_OPERACION.md
│   ├── 10_ANTIPATRONES.md
│   ├── RUNBOOK.md
│   └── SECURITY.md
├── agent/
│   ├── CLAUDE.md
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   │   ├── 0001_initial.py            ← customers, executions, agent_usage, queue
│   │   └── 0002_incident_schema.py    ← pendiente Sprint 1
│   ├── knowledge/                     ← BASE DE CONOCIMIENTO (read-only para el agente)
│   │   ├── faqs/
│   │   ├── technical/
│   │   ├── procedures/
│   │   └── known_issues/
│   └── src/agent/
│       ├── _logging.py
│       ├── api.py                     ← POST /api/incidents (Sprint 3)
│       ├── worker.py
│       ├── cli.py
│       ├── graph.py
│       ├── phases/
│       │   ├── 00_intake.py           ← phase_deterministic (Sprint 1)
│       │   ├── 01_classify.py         ← phase_light_llm (Sprint 1)
│       │   └── 02_escalate.py         ← phase_heavy_llm (Sprint 1)
│       ├── tools/
│       │   ├── _allowed.py
│       │   ├── check_duplicate.py     ← Sprint 1
│       │   ├── get_customer_context.py← Sprint 1
│       │   ├── search_knowledge_base.py← Sprint 1
│       │   ├── get_recent_incidents.py← Sprint 1
│       │   ├── write_log.py           ← Sprint 1
│       │   └── create_ticket.py       ← Sprint 1
│       ├── services/clients/
│       │   ├── kb_client.py           ← Sprint 1
│       │   └── storage_client.py      ← Sprint 1
│       ├── prompts/
│       │   ├── classifier-v1-2026-05-12.md
│       │   └── escalator-v1-2026-05-12.md
│       ├── schemas/
│       │   ├── input.schema.json
│       │   └── output.schema.json
│       ├── examples/
│       │   └── checkout_incident.json
│       ├── context/
│       │   ├── 01-mision.md
│       │   └── 02-criterio.md
│       └── roadmap/
│           ├── decisiones-pendientes.md
│           └── changelog.md
├── dashboard/
│   ├── CLAUDE.md
│   ├── src/app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── chat/                      ← Sprint 4
│   │   └── incidents/                 ← Sprint 4
│   └── src/lib/
│       ├── utils.ts
│       ├── db.ts                      ← Sprint 4
│       └── api.ts                     ← Sprint 4
└── .github/workflows/ci.yml
```

## Patrones de seguridad obligatorios

- **KB read-only:** `kb_client.py` solo abre ficheros en modo lectura. Sin writes en `agent/knowledge/`.
- **Bloqueo de tools en dos niveles:** dispatcher en `graph.py` verifica `ALLOWED_TOOLS_BY_PHASE` antes de invocar; la propia tool revalida `is_tool_allowed` como defence-in-depth.
- **Idempotencia:** `executions.UNIQUE(customer_id, external_id)` — `phase_deterministic` verifica antes de procesar.
- **Circuit breaker:** `OpenRouterClient(max_tokens_per_run=CIRCUIT_BREAKER_MAX_TOKENS)`.
- **Sin acciones destructivas:** el agente no ejecuta comandos sobre la plataforma ecommerce.
- **Storage centralizado:** todo write a `/Documentos/` pasa por `storage_client.py`.
