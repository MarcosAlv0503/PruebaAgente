# Proyecto: loang-template-agent

## Cliente

- **Tipo:** interno Loang. Es uno de los cuatro artefactos vivos del estándar Loang IA.
- **Sponsor:** Tech Lead Loang IA.
- **Mantenedor:** "Mantenedor del template" (rotación trimestral según playbook §4.10).

## Problema

Cuando el equipo arranca un proyecto de agente nuevo (interno o cliente externo), tiene que tomar 50+ decisiones de stack, estructura, herramientas, workflows, schemas. Sin un repo plantilla, cada proyecto reinventa esas decisiones, debate, y arranca lento. El template es esqueleto cableado: clonas, adaptas placeholders, y empiezas con el problema del cliente, no con el stack.

## Capacidades × modo (taxonomía playbook §3)

No aplica directamente — este artefacto **no es un agente**, es un repo plantilla. Pero está diseñado para servir cualquier combinación de capacidades 1-4 en cualquiera de los tres modos:

- Si el proyecto no tiene UI → el dev clona y borra `dashboard/`.
- Si el proyecto no usa Playwright → borra del Makefile y del `pyproject.toml` la dependencia.
- Si el proyecto es conversacional (no pipeline) → borra `agent/cli.py rn`/`rn-retry` y adapta `worker.py` a webhook.

## Volumetría asumida

| Métrica | Valor | Fuente |
|---|---|---|
| Proyectos que se crearán a partir del template a 12 meses | 5-10 | declarado |
| Tiempo de arranque tras `gh repo create --template` (a "make up" verde) | <30 min | objetivo |
| Tasa de adopción del template entre proyectos nuevos | 100% (es estándar) | obligatorio |
| Tamaño del repo clonado | <50 MB sin `node_modules` | objetivo |

## Stakeholders

- **Sponsor del estándar:** Tech Lead Loang IA.
- **Operadores finales:** los ~5 devs del equipo Loang IA al arrancar cada proyecto nuevo.
- **Indirectos:** clientes externos cuyos proyectos se construyen sobre el template.

## Alcance v0.1.x (MVP — esqueleto importable)

**Repo monorepo con backend Python + frontend Next.js + workflows + docs + Docker**, marcado como template en GitHub. v0.1.0 ship el subconjunto mínimo viable definido en ADR-002; v0.1.1+ aplican respuestas de auditoría externa sin ampliar alcance.

**Backend (`agent/`):**

- FastAPI con `/health` y endpoints stub (`501 Not Implemented`).
- Worker loop con `FOR UPDATE SKIP LOCKED` que reclama de `queue`, marca `executions.status='succeeded'` y libera la entrada.
- CLI con `python -m agent.cli run --customer <id>` y `retry --execution <id>`.
- LangGraph stub con tres fases canónicas (`deterministic` / `light_llm` / `heavy_llm`).
- `loang-toolkit @ v0.1.2` pinned vía `git+https`.
- Esqueleto de `phases/`, `tools/`, `prompts/`, `services/clients/`, `schemas/`, `examples/`, `context/`, `roadmap/`. Cada placeholder marcado para que `make verify-template-cleanup` lo detecte.
- Migración Alembic con 4 tablas base (`customers`, `executions`, `agent_usage`, `queue`); el resto de §13.16 (`issues`, `human_tasks`, `audit_log`) entra en v0.2.0.
- `Dockerfile` Python 3.13 slim con BuildKit secret para auth contra `loang-toolkit`.
- `agent/_logging.py` propio que emite JSON estructurado a stdout (mismo formato que el del toolkit).

**Frontend (`dashboard/`):**

- Next.js 15 App Router (rama 15.x con parches de seguridad aplicados) + TypeScript strict.
- Tailwind + un primitivo shadcn (`Button`) + helper `cn()`. Resto de primitivas se añaden cuando el proyecto las necesite.
- `<html lang="es">` por defecto (UI en español).
- Página `/` con landing placeholder y un botón.
- `Dockerfile` Node 20 slim.

**Infraestructura:**

- `docker-compose.yml` con servicios `agent`, `worker`, `dashboard`, `db` (Postgres 16) con healthchecks y BuildKit secret para `LOANG_TOOLKIT_TOKEN`.
- `.github/workflows/ci.yml` con jobs separados Python (lint + types + tests + cov ≥70%) y TypeScript (lint + typecheck + build).
- `Makefile` con targets `up`, `down`, `migrate`, `test` (incluye `npm run build`), `worker`, `rn`, `verify-template-cleanup` (gate, no informativo), `clean`, `check-python`.

**Documentación v0.1.x:**

- `CLAUDE.md` raíz, `agent/CLAUDE.md`, `dashboard/CLAUDE.md` con Top N anti-patrones.
- `docs/00_DECISIONES.md` con ADRs 1-4 (incluye ADR-002 que define el alcance v0.1.x).
- `docs/02_ARQUITECTURA.md`, `docs/03_AGENTE.md`, `docs/06_BASE_DATOS.md`, `docs/09_OPERACION.md`, `docs/10_ANTIPATRONES.md`, `docs/RUNBOOK.md`, `docs/SECURITY.md`.

**Claude Code:**

- `.claude/settings.json` con permisos bash + hook `UserPromptSubmit` que inyecta `COORDINACION.md` si existe.
- `.claude/commands/audit.md` (plantilla §13.15 adaptada).

**Marcado como template en GitHub:**

- `gh repo edit LoangIA/loang-template-agent --template` tras el primer commit (ya hecho en v0.1.0).

## Diferido a v0.2.0 (lo entra el primer proyecto cliente)

Por ADR-002, v0.1.x **no ship**:

- NextAuth integración full (proveedor + middleware + sesión persistida).
- Sentry SDK Python + Next.
- Drizzle Kit `introspect` para tipos TS desde el schema BD.
- Playwright smoke tests del dashboard.
- `fly.toml` y `.github/workflows/deploy.yml`.
- Tablas `issues`, `human_tasks`, `audit_log`.
- shadcn primitives extra (`Input`, `Card`, `Table`, `Toast`, `Form`).
- Slash commands `adr.md` y `phase-close.md`.
- `docs/04_MODELOS_COSTES.md`, `docs/05_DOMINIO.md`, `docs/07_BACKEND.md`, `docs/08_FRONTEND.md`, `docs/11_LENGUAJE_VISUAL.md`.
- Dispatcher de tools con deny-by-default (la whitelist `ALLOWED_TOOLS_BY_PHASE` ya está; falta el dispatcher que la haga vinculante).
- CLI `INSERT ... ON CONFLICT (customer_id, external_id)` para idempotencia operativa (la `UNIQUE` constraint ya está en schema).

## Fuera de alcance v1 (a v2 tras primer proyecto adoptante)

- Workflow de mantenimiento del template (cómo se actualiza cuando el playbook v1 → v2).
- Bot de "drift detection" que avisa a proyectos clonados cuando el template cambia.
- Variantes de template por capacidad principal (browser-only, conversacional-only) — por ahora un único template multi-uso.

## Decisiones de stack para este proyecto

Aplica el estándar del playbook §4.2 entero. Sin desviaciones. Es **el** template del estándar — desviarse sería contradecir el propio playbook.

## Hitos

- **Fase 1 cerrada:** esqueleto + workflows + repo creado y marcado como template + tag `v0.1.0`. Objetivo: ≤10h de un técnico, antes de los 15 días desde arranque.
- **Auditoría externa Fase 1:** sesión Claude Code nueva con plantilla §13.15 del playbook.
- **Smoke test del template:** crear un proyecto piloto desechable a partir del template (`gh repo create loang-test-piloto --template ...`), seguir el flujo del playbook §6.3 sobre él, comprobar que arranca con `make up` y `make test` verde sin tocar nada. Si falla, fix en el template.
- **Adopción real:** primer proyecto cliente externo arranca a partir del template. Ese proyecto es **caso piloto del playbook entero** (playbook §15.3) y su retrospectiva alimenta v2 del template.
- **v0.2.0 del template:** tras el primer proyecto cliente real, ajustes de placeholders y workflows. ~5h adicionales.

## Riesgos identificados y mitigaciones

- **El template envejece** cuando el stack avanza (Next.js 16 estable, etc.). Mitigación: revisión trimestral conjunta con el playbook §4.8.
- **Proyectos clonados divergen del template** y luego son difíciles de auditar. Mitigación: `CLAUDE.md` raíz del template documenta qué es heredado vs adaptable; ADR del proyecto al desviarse.
- **`loang-toolkit` cambia API y rompe el template.** Mitigación: pin de versión exacta (`@v0.1.0`), bump deliberado en cada revisión.
- **Auth `git+https`/`git+ssh` no cuadra en CI de proyectos consumidores.** Mitigación: `docs/09_OPERACION.md` documenta paso a paso cómo configurar el PAT y el secret BuildKit en cada repo nuevo.
- **El template incluye tantos placeholders que el dev del proyecto los pasa por alto.** Mitigación: `make verify-template-cleanup` falla con exit 1 si quedan marcadores `TODO loang-template` (en cualquier formato) o ficheros `_example.*`.

## Cómo evoluciona

- Cambios al template se proponen como issues en su repo. Aprobación del mantenedor.
- Cada release incluye `CHANGELOG.md` actualizado y nota sobre si es retrocompatible para proyectos ya clonados.
- Revisión trimestral conjunta con el playbook (playbook §4.8): qué placeholders generaron fricción, qué patrones nuevos del playbook hay que incorporar, qué dependencias hay que bumpar.
