# loang-template-agent

> Repo plantilla GitHub privado. Punto de partida de cualquier proyecto de agente nuevo de Grupo Loang. Acompaña al Playbook Loang de Construcción de Agentes (v1).

## Estado actual

Fase 1 — Esqueleto. En construcción inicial. Última actualización: arranque del proyecto.

## Top 6 cosas que NO hacer

1. **No metas lógica de negocio del agente.** El template es esqueleto cableado, no un agente real. Cada placeholder está marcado con `# TODO loang-template:` para que el dev del proyecto que clona sepa qué adaptar y qué borrar. Consecuencia: el template se acopla a un proyecto concreto y deja de ser reusable.
2. **No actualices versiones major del stack** sin ADR del playbook. Next.js 15 (no 16), Python 3.13 (no 3.14), NextAuth v5 estable (no beta). Consecuencia: proyectos clonados heredan inestabilidades y rompen 2 años después.
3. **No metas el `loang-toolkit` con `pip install -e .`.** Se importa con `pip install git+ssh://...@v<X.Y.Z>` con tag pinned. Consecuencia: proyectos clonados quedan colgados de un fork local del toolkit.
4. **No commitees `.env`, ni claves, ni la `FERNET_KEY` del template** aunque sea de ejemplo. Solo `.env.example`. Consecuencia: pwn.
5. **No hagas el `agent/context/` con contenido real.** Deja placeholders genéricos que cada proyecto rellena (ver §13 del playbook). Consecuencia: el template "habla" de un dominio que no es el del proyecto que lo clona.
6. **No mezcles UI del dashboard en inglés y español.** UI siempre en español (cliente final hispanohablante por defecto del playbook). Si el proyecto necesita inglés, ADR del proyecto que lo clona. Consecuencia: i18n a medias en cada proyecto clonado.

## Stack del proyecto

| Capa | Elección | Notas |
|---|---|---|
| Lenguaje del agente | Python 3.13 | |
| Orquestación LLM | LangGraph | |
| Pasarela de modelos | OpenRouter vía `loang-toolkit.OpenRouterClient` | |
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
| Auth | NextAuth v5 estable | |
| Plataforma cloud | Fly.io | Región `mad` por defecto |
| Orquestación local | Docker Compose | |
| Observabilidad | Sentry (Python + Next) | |
| Logs | JSON estructurados a stdout | Formato `[component] message` |
| Browser automation | Playwright sync (cuando aplique) | |

(Desviaciones del estándar del playbook: ver `docs/00_DECISIONES.md`.)

## Convenciones no negociables

- Idioma del código: inglés (variables, funciones, comentarios, schema BD, slash commands, logs, commits).
- Idioma de la UI del dashboard: español (cliente final hispanohablante).
- Idioma de la documentación (`docs/`, `CLAUDE.md`, prosa): español.
- Tipos: `mypy strict` en Python, `strict: true` en TS. Sin `any` ni `Any`.
- Logs: JSON estructurados a stdout, formato `[component] message`.
- Commits: `<type>: <description>` en inglés.

## Comandos esenciales

```bash
make up          # arranca todos los servicios (docker-compose)
make migrate     # aplica migraciones Alembic
make test        # tests + lint + types (Python + TS)
make rn ID=123   # ejecuta una unidad de trabajo concreta del agente (placeholder)
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
| Lenguaje visual del cliente | `11_LENGUAJE_VISUAL.md` |
| Seguridad | `SECURITY.md` |

## Coordinación entre devs

Si el proyecto que clona este template trabaja con dos terminales Claude Code en paralelo (típico: uno en `agent/`, otro en `dashboard/`), copia `COORDINACION.md.template` a `COORDINACION.md` en raíz y mantenlo actualizado. El hook `UserPromptSubmit` configurado en `.claude/settings.json` lo inyecta automáticamente al contexto.

## Cómo se usa este template

```bash
# Crear un proyecto nuevo a partir del template
gh repo create loang-<proyecto> --template grupoloang/loang-template-agent --private
cd loang-<proyecto>

# Adaptar
# 1. Editar CLAUDE.md raíz: rellenar Top N anti-patrones del proyecto, stack si difiere.
# 2. Editar docs/01_PROYECTO.md con cliente, problema, capacidades x modo, volumetría, hitos.
# 3. Editar agent/context/01-mision.md con la misión del agente concreto.
# 4. Borrar lo que no se use (ej. dashboard/ si es agente puro batch sin UI).
# 5. Renombrar referencias internas de "loang-template" a "loang-<proyecto>".
# 6. Configurar Fly.io: fly launch + fly secrets.
# 7. Primer prompt a Claude Code: usar plantilla §13.14 del playbook adaptada a este proyecto.
```

## Estructura del repo

```
loang-template-agent/
├── CLAUDE.md                          ← este archivo
├── README.md                          ← cómo se usa el template
├── docker-compose.yml
├── .env.example
├── .gitignore
├── COORDINACION.md.template           ← se copia a COORDINACION.md cuando hay >1 dev
├── Makefile
├── .claude/
│   ├── settings.json                  ← permisos bash + hook UserPromptSubmit
│   └── commands/
│       └── audit.md                   ← plantilla §13.15 (auditoría externa)
├── docs/
│   ├── 00_DECISIONES.md               ← ADR vivo (template arranca con 4 ADRs)
│   ├── 01_PROYECTO.md                 ← rellenar al clonar
│   ├── 02_ARQUITECTURA.md
│   ├── 03_AGENTE.md
│   ├── 06_BASE_DATOS.md
│   ├── 09_OPERACION.md
│   ├── 10_ANTIPATRONES.md
│   ├── RUNBOOK.md
│   └── SECURITY.md
├── agent/
│   ├── CLAUDE.md                      ← convenciones del agente
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial.py        ← schema base 4 tablas (playbook §13.16 parcial)
│   ├── src/
│   │   └── agent/
│   │       ├── __init__.py
│   │       ├── _logging.py            ← JSON logger del agente
│   │       ├── api.py                 ← FastAPI app
│   │       ├── worker.py              ← worker loop
│   │       ├── cli.py                 ← entrada CLI (make rn, make rn-retry)
│   │       ├── graph.py               ← LangGraph stub
│   │       ├── phases/
│   │       │   ├── __init__.py
│   │       │   └── _example.py        ← placeholder + comentario para borrar
│   │       ├── tools/
│   │       │   ├── __init__.py
│   │       │   └── _allowed.py        ← whitelist por fase (sin dispatcher en v0.1.x)
│   │       ├── prompts/
│   │       │   └── _example-v1-2026-04-29.md  ← placeholder con front-matter
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   └── clients/
│   │       │       └── __init__.py    ← placeholder; cada proyecto añade clients/<provider>.py
│   │       ├── schemas/
│   │       │   ├── input.schema.json  ← schema base genérico
│   │       │   └── output.schema.json
│   │       ├── examples/
│   │       │   └── _example.json      ← placeholder
│   │       ├── context/
│   │       │   ├── 01-mision.md       ← rellenar al clonar
│   │       │   └── 02-criterio.md
│   │       └── roadmap/
│   │           ├── decisiones-pendientes.md
│   │           └── changelog.md
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_smoke.py              ← imports + lifecycle + schemas + prompts
│   └── Dockerfile
├── dashboard/
│   ├── CLAUDE.md
│   ├── package.json                   ← Next.js 15 + Tailwind + class-variance-authority
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .eslintrc.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   └── ui/
│   │   │       └── button.tsx         ← única primitiva shadcn en v0.1.x
│   │   ├── lib/
│   │   │   └── utils.ts               ← cn() helper para shadcn
│   │   └── styles/
│   │       └── globals.css
│   └── Dockerfile
├── docker-compose.yml                 ← db + agent + worker + dashboard (BuildKit secret)
├── COORDINACION.md.template
├── CHANGELOG.md
└── .github/
    └── workflows/
        └── ci.yml                     ← lint + types + tests + build en cada PR
```

**Diferido a v0.2.0** y por tanto **no presentes** en el árbol actual (ver ADR-002):
`.claude/commands/{adr.md,phase-close.md}`, `docs/{04_MODELOS_COSTES,05_DOMINIO,07_BACKEND,08_FRONTEND,11_LENGUAJE_VISUAL}.md`, `dashboard/components.json`, `dashboard/drizzle.config.ts`, `dashboard/src/app/api/auth/[...nextauth]/route.ts`, `dashboard/src/lib/{db.ts,api.ts,auth.ts}`, `dashboard/tests/`, `fly.toml`, `.github/workflows/deploy.yml`, schema completo (`issues`, `human_tasks`, `audit_log`).

## Patrones obligatorios pre-cableados

Cuando un proyecto clona este template, hereda automáticamente:

- **Multi-modelo por fase**: estructura `phases/` con whitelist por fase (`tools/_allowed.py`).
- **Bloqueo de tools en dos niveles**: hook en el dispatcher que valida contra `_allowed.py`.
- **Token tracking + circuit breaker**: importa `loang-toolkit.OpenRouterClient` ya configurado.
- **Cliente único centralizado**: `services/clients/` con interfaz de dominio.
- **Idempotencia por `external_id`**: schema `executions` con `UNIQUE(customer_id, external_id)`.
- **Resumen consolidado entre fases**: helper `build_summary(state) -> str` stub.
- **`COORDINACION.md` con hook**: `.claude/settings.json` ya configurado.
- **Top N anti-patrones en `CLAUDE.md`**: estructura puesta, contenido vacío para que el proyecto rellene.
- **Schemas JSON formales**: `agent/schemas/` con `additionalProperties: false`.
- **Prompts versionados**: `agent/prompts/<role>-v<n>-<YYYY-MM-DD>.md` con front-matter YAML.
- **`agent/roadmap/decisiones-pendientes.md`** con etiquetas.
- **`agent/roadmap/changelog.md`** con formato fijo.

## Convenciones del template (no del proyecto que lo clona)

- Cada placeholder tiene comentario `# TODO loang-template: ...` que el proyecto que clona busca con `rg "TODO loang-template"` y resuelve uno a uno.
- Cada archivo `_example.*` se borra cuando el proyecto añade el real.
- Versionado del template: tag `v0.1.0` al cierre Fase 1, semver desde ahí. Cuando el template cambia, los proyectos ya clonados no se actualizan automáticamente — es decisión de cada proyecto si cherry-pickea cambios del template.
