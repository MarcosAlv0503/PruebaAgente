# Changelog

Todas las versiones siguen [SemVer pre-1.0](docs/00_DECISIONES.md#adr-001--stack-del-template--estándar-loang-sin-desviaciones). El alcance v0.1.x está fijado por ADR-002.

## [0.1.1] — 2026-04-29

Patch tras la primera auditoría externa (Codex GPT). Cierra los cuatro hallazgos críticos y los medios baratos; los dos medios que requieren primer proyecto cliente quedan en backlog.

### Fixed

- **C1 — Stack reproducible.** `Makefile` ahora exige `python3.13` exacto vía `make check-python` (falla si está activo 3.14). `agent/pyproject.toml` añade `requires-python = ">=3.13,<3.14"` y techos major en todas las dependencias (`fastapi<1`, `uvicorn<1`, `psycopg<4`, `alembic<2`, `pydantic<3`, `httpx<1`, `langgraph<2`). Sin esto, `langgraph>=0.2` resolvía a `1.x` sin ADR; un proyecto cliente fresco quedaba fuera del estándar Loang sin darse cuenta.
- **C2 — Logs JSON estructurados.** Nuevo `agent/_logging.py` que replica el formato del `loang_toolkit._logging` (mismas claves: `timestamp`, `level`, `component`, `message` con prefijo `[component]`). `worker.py`, `cli.py` y `graph.py` usan `agent._logging.get_logger("<component>")` en lugar de `logging.basicConfig` + `logging.getLogger("loang_toolkit.*")`. Decisión: usar logger propio en vez de importar de `loang_toolkit._logging` (privado) — exponer ese símbolo desde el toolkit espera a tener un consumidor real que lo pida.
- **C3 — `verify-template-cleanup` ahora es gate.** Reescrito el target para salir con exit 1 si quedan marcadores `TODO loang-template` (en cualquier formato, no solo `# `/`// `) o ficheros `_example.*`. Allowlist los archivos que documentan el patrón en prosa (`Makefile`, `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `docs/`).
- **C4 — Docker autenticado contra `loang-toolkit` privado.** `agent/Dockerfile` usa `RUN --mount=type=secret,id=loang_toolkit_token` (BuildKit) y `docker-compose.yml` declara el secret leyendo `LOANG_TOOLKIT_TOKEN` del entorno. El token nunca queda en una capa de imagen. `Makefile` exporta `DOCKER_BUILDKIT=1` automáticamente en `make up`. `.env.example` documenta `LOANG_TOOLKIT_TOKEN` con instrucción de usar `gh auth token` localmente.
- **M3 — Worker cierra el lifecycle de la ejecución.** `_handle_execution` ahora actualiza `executions.status='succeeded'` con `output={"stub": true}`, rellena `started_at`/`finished_at` y borra la fila de `queue`. Antes dejaba ejecuciones reclamadas indefinidamente como "running" sin liberar la cola.
- **M6 — `make test` incluye `npm run build`.** Nuevo target `build-frontend` invocado desde `test`. CI ya lo hacía; localmente se podía pasar `make test` y romper en CI por un build de Next.js fallando.

### Added

- **`docs/SECURITY.md`** con modelo de amenazas v0.1.x, manejo de secretos (incluye `LOANG_TOOLKIT_TOKEN`), checklist de release del proyecto cliente y reglas para PII en pruebas.

### Documentation

- **M1 — Árbol de `CLAUDE.md` y alcance de `docs/01_PROYECTO.md` alineados con la realidad v0.1.0.** Ambos listaban `fly.toml`, `deploy.yml`, NextAuth route, Drizzle config, slash commands `adr.md`/`phase-close.md`, primitivas shadcn extra y docs `04`/`05`/`07`/`08`/`11` como si existieran. Ahora reflejan el árbol real y enumeran lo diferido a v0.2.0 en una sección dedicada.
- **README.md** actualizado: el toolkit se instala vía `git+https` (con PAT), no `git+ssh`. Pre-requisito de Python ahora dice 3.13 (no 3.13+), alineado con el guard del Makefile.
- **`agent/CLAUDE.md`** actualiza la convención de logging para reflejar `agent._logging.get_logger` (no `loang_toolkit._logging`, que es módulo privado).

### Tests

- Nuevo test del worker que verifica el warning cuando `DATABASE_URL` no está configurado (camino que no estaba cubierto).
- Cobertura backend: 76%.

### Deferred to v0.2.0 (audit-fase-1 issues)

- **M2 — Dispatcher de tools con deny-by-default.** La whitelist `ALLOWED_TOOLS_BY_PHASE` está, pero falta el dispatcher que la haga vinculante. Diseñarlo sin tools reales del primer proyecto cliente sería abstraer ahead of need. Issue tracked.
- **M4 — `INSERT ... ON CONFLICT (customer_id, external_id)` en `cli.py`.** El schema ya tiene la `UNIQUE`; falta que la CLI demuestre el patrón de idempotencia. Mismo argumento — esperar al primer webhook real. Issue tracked.

### Calibración del informe Codex

- **C2 calibrado de crítico a medio**: la convención violada se documenta y se arregla, pero no bloqueaba adopción.
- **m1 (e-commerce en `_example`)**: aplicado — `pedido`/`order_id`/`Ana` reemplazado por `<domain_event>`/`{entity_id}`.
- **m2 (README dice SSH, pyproject usa HTTPS)**: aplicado, README ahora dice HTTPS.
- **m3 (`experimental.typedRoutes` warning)**: aplicado, `next.config.js` lo retira para builds silenciosos.

## [0.1.0] — 2026-04-29

### Added

- Release inicial del template. Esqueleto mínimo viable según ADR-002: backend FastAPI + LangGraph stub + Postgres con 4 tablas base + frontend Next.js 14 con un primitivo shadcn + CI con jobs Python y TypeScript + 4 ADRs + 7 documentos.
- `loang-toolkit @ v0.1.2` pinned como dep.
- Repo marcado como GitHub template (`isTemplate: true`).
