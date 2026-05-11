# Arquitectura — `loang-template-agent`

## Vista general

```
                  ┌─────────────────────┐
                  │   Operador interno  │
                  │   (navegador)       │
                  └──────────┬──────────┘
                             │ HTTPS
                             ▼
                   ┌─────────────────────┐
                   │  dashboard          │
                   │  Next.js 15         │
                   │  :3000              │
                   └──────────┬──────────┘
                              │ HTTP (interno)
                              ▼
                   ┌─────────────────────┐
                   │  agent/api          │
                   │  FastAPI            │
                   │  :8000              │
                   └──────────┬──────────┘
                              │ SQL (psycopg)
                              ▼
              ┌─────────────────────────────────┐
              │  Postgres 16                    │
              │  customers / executions /       │
              │  agent_usage / queue            │
              └──────────┬──────────────────────┘
                         │ SELECT FOR UPDATE SKIP LOCKED
                         │
                         ▼
                  ┌─────────────────────┐
                  │  agent/worker       │
                  │  loop (cada 5s)     │
                  └──────────┬──────────┘
                             │ HTTPS
                             ▼
                  ┌─────────────────────┐
                  │  OpenRouter         │
                  │  (vía              │
                  │  loang_toolkit.     │
                  │  OpenRouterClient)  │
                  └─────────────────────┘
```

## Componentes y responsabilidades

| Componente | Responsabilidad | Lo que NO hace |
|---|---|---|
| `dashboard/` (Next.js) | UI para operador. Lectura de la BD vía `lib/db.ts` (pool readonly). Escrituras vía `lib/api.ts` (llama al backend FastAPI). | No invoca al LLM. No corre lógica de agente. |
| `agent/api` (FastAPI) | Endpoint HTTP de control: `/health`, cancelación, escalación humana. Crea ejecuciones e issues. | No corre lógica de fase pesada — encola y delega al worker. |
| `agent/worker` (Python loop) | Reclama trabajo de `queue` con `FOR UPDATE SKIP LOCKED`. Invoca `agent.graph.run(state)`. | No abre conexiones a sistemas externos directamente — usa `services/clients/`. |
| `agent/graph` (LangGraph) | Driver de las tres fases. Decide el routing entre `deterministic` → `light_llm` → `heavy_llm`. | No conoce los detalles de cada fase — solo las invoca. |
| `agent/phases/` | Lógica de negocio por fase. Funciones puras `(state) -> state`. | No abre HTTP ni BD — recibe lo que necesita en `state`. |
| `agent/services/clients/` | Adaptadores a sistemas externos del cliente final (CRM, billing, mensajería). Un módulo por proveedor. | No mezcla varios proveedores en un módulo — single-centralised-client (playbook §5.1.7). |
| `loang_toolkit` | Utilidades transversales: token tracking, redacción PII, OpenRouter client, prompt loader. | Imported as a pinned dep, never modified inside this repo. |

## Separación dashboard ↔ agente

Estricta:

- **El dashboard nunca llama al LLM directamente.** Si necesita cobrar coste de tokens en una vista, los lee de `agent_usage` vía `lib/db.ts`.
- **El agente nunca renderiza HTML.** Devuelve JSON (validado contra `output.schema.json`) y la UI lo presenta.
- **Únicas escrituras desde el dashboard:** llamadas POST/PUT al backend FastAPI. Cualquier mutación en BD pasa por `agent/api/...`.

Razón: si el dashboard escribe directo a BD, evolucionas dos lógicas de validación en paralelo (frontend y backend) y se desincronizan en el primer cambio de schema.

## Flujo "ejecutar trabajo"

1. Algo (CLI, webhook, dashboard) llama a `POST /api/executions/...` (en v0.1.0: `make rn ID=<customer-id>` desde CLI).
2. `agent/api` o `agent/cli` crea row en `executions` (`status='pending'`) y `queue`.
3. `agent/worker` reclama el row con `UPDATE ... RETURNING execution_id`.
4. El worker llama a `agent.graph.run(state)`.
5. `agent.graph` llama a `phase_deterministic`, luego `phase_light_llm`, opcionalmente `phase_heavy_llm`.
6. Cada fase LLM usa `loang_toolkit.OpenRouterClient(tracker=tracker, ...)` para invocar el modelo. El tracker persiste en `agent_usage`.
7. El worker actualiza `executions.status` a `'succeeded'` / `'failed'` y libera la entrada de `queue`.

## Bloqueo de tools en dos niveles

Patrón del playbook §5.1.2. Una tool es invocable solo si:

- Su nombre está en `ALLOWED_TOOLS_BY_PHASE[phase]` (verificado por el dispatcher antes de llamar).
- La propia tool revalida fase activa antes de actuar (defence-in-depth).

v0.1.0 ship `ALLOWED_TOOLS_BY_PHASE` vacío; cada proyecto añade tools con su whitelist explícita.

## Convención de errores

| Excepción | Origen | Acción esperada |
|---|---|---|
| `ValueError` | Argumento inválido en código del agente. | Bug del dev. |
| `psycopg.Error` | Fallo de BD. | Worker reintenta vía cola (atributo `attempts`). Si supera N, mueve a `human_tasks` (v0.2.0). |
| `loang_toolkit.CircuitBreakerError` | Coste runaway. | Worker termina la ejecución con `status='failed'` y `error='budget_exceeded'`. |
| `httpx.HTTPStatusError` (4xx) | Bug en payload a OpenRouter. | Worker no reintenta; `status='failed'`. |

## No-objetivos arquitecturales del template v0.1.0

- **No incluye autenticación real.** NextAuth solo está como dep planeada; el provider lo configura cada proyecto cliente (ver ADR-002, deferido).
- **No incluye observabilidad real.** Sentry deferido a v0.2.0.
- **No incluye deploy automatizado.** `fly.toml` y `deploy.yml` deferidos a v0.2.0; el primer proyecto que despliegue informa qué necesita.
