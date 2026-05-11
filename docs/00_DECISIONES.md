# Decisiones arquitecturales (ADRs) — `loang-template-agent`

Cada ADR documenta una decisión cerrada y su consecuencia. Si una utilidad o componente nuevo exige una decisión, se añade aquí antes de tocar código.

## ADR-001 — Stack del template = estándar Loang sin desviaciones

**Fecha:** 2026-04-29.

**Estado:** Aceptado.

**Contexto.** Este repo es **el template** del estándar Loang IA. Los proyectos cliente lo clonan con `gh repo create --template`. Cualquier desviación del stack del playbook §4.2 que no se justifique aquí se propaga automáticamente a todos los proyectos derivados.

**Decisión.** El template se ciñe a la versión estándar del stack del playbook v1: Python 3.13 + FastAPI + LangGraph + psycopg 3 + Alembic + Postgres 16 + Next.js 15 (App Router) + TypeScript strict + Tailwind + shadcn/ui + NextAuth v5 + Fly.io + Docker Compose + Sentry + Playwright. Cualquier upgrade major (Next.js 16, Python 3.14, NextAuth beta) requiere ADR del playbook, no de este template.

**Consecuencias.** Proyectos clonados heredan el stack sin negociación. Si un proyecto cliente necesita otro stack, abre ADR de proyecto justificándolo y no usa este template.

## ADR-002 — Alcance v0.1.0 reducido al esqueleto importable

**Fecha:** 2026-04-29.

**Estado:** Aceptado.

**Contexto.** El `PROMPT_INICIAL` original especificaba un template con NextAuth integración completa, Sentry, Drizzle Kit `introspect`, Playwright, `fly.toml` + `deploy.yml`, schema completo (`issues`, `human_tasks`, `audit_log`), 13 documentos `docs/` y dos slash commands extra (`adr.md`, `phase-close.md`). Un alcance así pre-decide muchas cosas para un primer proyecto cliente que aún no existe — exactamente el anti-patrón "refinar abstracciones antes de tener fricción real" que el playbook §5.1 advierte.

**Decisión.** v0.1.0 ship únicamente lo necesario para que un primer proyecto cliente arranque:

- Backend FastAPI con `/health` + endpoints stub (`501 Not Implemented`).
- Worker loop estable que reclama de `queue` con `FOR UPDATE SKIP LOCKED`.
- CLI con `run` y `retry`.
- LangGraph stub con tres fases canónicas (`deterministic` / `light_llm` / `heavy_llm`).
- Schema base 4 tablas: `customers`, `executions`, `agent_usage`, `queue` (de las 7 que pide §13.16).
- Dashboard Next.js minimal: una landing con un botón shadcn (Button único, no todas las primitivas).
- `loang-toolkit@v0.1.2` pinned como dep.
- CI con dos jobs (agent + dashboard).
- Docs: `00_DECISIONES.md`, `01_PROYECTO.md`, `02_ARQUITECTURA.md`, `03_AGENTE.md`, `06_BASE_DATOS.md`, `09_OPERACION.md`, `10_ANTIPATRONES.md`, `RUNBOOK.md`.
- Slash command: `audit.md`.

**Diferido a v0.2.0** (lo entran proyectos cliente con fricción real):

- NextAuth integración full (proveedor + middleware + sesión persistida).
- Sentry SDK Python + Next.
- Drizzle Kit `introspect` para tipos TS desde el schema.
- Playwright smoke tests.
- `fly.toml` + `.github/workflows/deploy.yml` (deploy automatizado).
- Tablas `issues`, `human_tasks`, `audit_log`.
- shadcn primitives extra (Input, Card, Table, Toast, Form).
- Slash commands `adr.md` y `phase-close.md`.
- Docs `04_MODELOS_COSTES.md`, `05_DOMINIO.md`, `07_BACKEND.md`, `08_FRONTEND.md`, `11_LENGUAJE_VISUAL.md`, `SECURITY.md` extendidos.

**Consecuencias.**

- Un proyecto cliente que clone v0.1.0 necesita configurar Fly.io, Sentry, NextAuth y schemas adicionales por su cuenta. La fricción real informa qué entra en v0.2.0 del template.
- El template no pretende cubrir todos los casos al primer intento; se gana iterativamente con uso.

## ADR-003 — Schema BD en inglés según playbook §13.16

**Fecha:** 2026-04-29.

**Estado:** Aceptado.

**Contexto.** Necesitamos uniformidad de schemas a nivel del estándar Loang para que la columna `cost_usd` en `agent_usage` o el estado `succeeded` en `executions` tengan el mismo nombre en todo proyecto Loang. Eso permite correlación cross-proyecto y reusar utilidades como `loang_toolkit.TokenTracker` sin reescribir queries.

**Decisión.** Tablas, columnas, estados y severidades en inglés. UI del dashboard en español (cliente final hispanohablante), pero todo lo que toque la BD usa identificadores ingleses. El schema arranca con 4 tablas — el resto (`issues`, `human_tasks`, `audit_log`) entran cuando un proyecto cliente las necesite (ADR-002).

**Consecuencias.**

- `loang_toolkit.TokenTracker` apunta a la tabla `agent_usage` por defecto y la migración `0001_initial.py` la crea con esos nombres exactos.
- Proyectos cliente que añadan columnas locales lo hacen en migraciones nuevas; no renombran las base.

## ADR-004 — Idioma del código en inglés, UI en español, docs en español

**Fecha:** 2026-04-29.

**Estado:** Aceptado.

**Contexto.** La rotación de devs y la integración con SDKs/librerías en inglés hacen impracticable mantener identificadores en español. Pero el cliente final del proyecto (operador del dashboard, usuario hispanohablante) necesita la UI en su idioma. Y el equipo Loang trabaja la documentación en español.

**Decisión.** Tres idiomas, una regla por capa:

- **Código:** inglés. Variables, funciones, métodos, clases, comentarios, docstrings, mensajes de log, mensajes de commit, schemas pydantic, schemas JSON, slash commands.
- **UI:** español por defecto (cliente final hispanohablante). Si el proyecto cliente necesita inglés u otro, ADR del proyecto.
- **Documentación:** español. `docs/`, `CLAUDE.md`, prosa de README, ADRs.

**Consecuencias.**

- Convención uniforme por capa: el dev no improvisa.
- Si un proyecto cliente necesita UI multilingüe (ej. cliente con sedes en varios países), abre ADR del proyecto e introduce i18n con `next-intl` u otro.
