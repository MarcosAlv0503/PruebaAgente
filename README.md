# loang-template-agent

> Plantilla GitHub privada de Grupo Loang IA para arrancar cualquier proyecto de agente nuevo. Acompaña al [Playbook Loang de Construcción de Agentes (v1)](https://www.notion.so/Playbook-Creaci-n-de-Agentes-3425d5fd658581509407e1fe07f46da8).

Stack: FastAPI + LangGraph + Postgres + Next.js 15 (App Router) + Tailwind + shadcn/ui. Importa [`loang-toolkit`](https://github.com/LoangIA/loang-toolkit) con tag pinned para tracking de tokens, redacción de PII, cliente OpenRouter y carga de prompts versionados.

## Cómo se usa

```bash
gh repo create loang-<proyecto> --template LoangIA/loang-template-agent --private
cd loang-<proyecto>
```

## Adaptar tras clonar

Lista numerada que el dev del proyecto que clona ejecuta uno a uno:

1. **Editar [`CLAUDE.md`](CLAUDE.md)** raíz: rellenar el bloque "Top N anti-patrones" con los del proyecto, ajustar stack si difiere.
2. **Editar [`docs/01_PROYECTO.md`](docs/01_PROYECTO.md)**: cliente, problema, capacidades × modo (taxonomía playbook §3), volumetría, stakeholders, alcance v1, hitos.
3. **Editar [`agent/src/agent/context/01-mision.md`](agent/src/agent/context/01-mision.md)** con la misión concreta del agente.
4. **Borrar lo que no se use.** Si el proyecto es batch puro sin UI, borra [`dashboard/`](dashboard/). Si no usa Postgres, borra [`agent/alembic/`](agent/alembic/) y ajusta [`docker-compose.yml`](docker-compose.yml).
5. **Renombrar referencias.** `rg "loang-template" .` y reemplaza por `loang-<proyecto>`.
6. **Configurar Fly.io** cuando llegue el momento de deploy: `fly launch && fly secrets set ...`.
7. **Resolver placeholders del template.** `make verify-template-cleanup` lista cada `# TODO loang-template:` o `// TODO loang-template:` que aún quede sin tocar.
8. **Primer prompt a Claude Code:** usar plantilla §13.14 del playbook adaptada al proyecto.

## Pre-requisitos

- Python 3.13 (no 3.14 — el `Makefile` lo enforza vía `make check-python`)
- Node 20+
- Docker + Docker Compose (para `make up` local; `DOCKER_BUILDKIT=1` automático)
- `gh` CLI autenticado contra `LoangIA`
- Acceso de lectura a [`LoangIA/loang-toolkit`](https://github.com/LoangIA/loang-toolkit) (la dependencia se instala vía `git+https` con un PAT — ver `docs/09_OPERACION.md`)

## Comandos esenciales

```bash
make up                # arranca db + agent + dashboard en docker compose
make down              # tira los servicios
make migrate           # aplica migraciones Alembic en la BD
make test              # lint + types + tests (Python y TypeScript)
make rn ID=123         # ejecuta una unidad de trabajo del agente (placeholder)
make verify-template-cleanup  # lista TODO loang-template pendientes
```

## Documentación de referencia

- [`CLAUDE.md`](CLAUDE.md) — contexto raíz para Claude Code.
- [`docs/00_DECISIONES.md`](docs/00_DECISIONES.md) — ADRs vivos, arrancan con 4.
- [`docs/02_ARQUITECTURA.md`](docs/02_ARQUITECTURA.md) — diagrama agent ↔ worker ↔ dashboard ↔ db.
- [`docs/06_BASE_DATOS.md`](docs/06_BASE_DATOS.md) — schema base + cómo añadir migraciones.
- [`docs/09_OPERACION.md`](docs/09_OPERACION.md) — local + deploy + secretos.
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — operativa diaria.

## Estado actual

**v0.1.0 — esqueleto mínimo viable.** Pre-cableado: `loang-toolkit@v0.1.2` pinned, schema base 4 tablas (`customers`, `executions`, `agent_usage`, `queue`), FastAPI con `/health`, worker stub, LangGraph stub de tres fases, dashboard Next.js con un botón shadcn, CI verde.

**Diferido a v0.2.0** (tras feedback del primer proyecto cliente): NextAuth integración completa, Sentry, Drizzle Kit `introspect`, Playwright smoke tests, `fly.toml` + `deploy.yml`, slash commands `adr.md` / `phase-close.md`, schema completo §13.16 con `issues` / `human_tasks` / `audit_log`, docs `04_MODELOS_COSTES`, `05_DOMINIO`, `07_BACKEND`, `08_FRONTEND`, `11_LENGUAJE_VISUAL`, `SECURITY.md`. Ver [`docs/00_DECISIONES.md`](docs/00_DECISIONES.md) ADR-002.

## Licencia

Privado. Uso interno de Grupo Loang IA y de los proyectos derivados del estándar Loang.
