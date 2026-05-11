# Política de seguridad — `loang-template-agent`

## Reporte de vulnerabilidades

Si encuentras una vulnerabilidad en el template (o en un proyecto cliente derivado), **no abras issue público**. Escribe a `tech@loangia.com` con:

- Versión afectada (tag/commit) o repo cliente.
- Descripción del problema y vector de explotación.
- Repro mínimo si lo tienes.

Compromiso de respuesta: acuse en 48h hábiles, plan de fix en 5 días hábiles.

## Modelo de amenazas v0.1.x

El template arranca un repo monorepo con backend Python, frontend Next.js y BD Postgres. Sus superficies con exposición:

| Componente | Riesgo | Mitigación actual |
|---|---|---|
| `agent/api` (FastAPI) | Endpoints stub que devuelven `501`. En cuanto el proyecto los implemente, la superficie crece (auth, validación de input, rate limit). | v0.1.x ship `/health` + stubs documentados. NextAuth integration completa diferida a v0.2.0 (ADR-002). |
| `agent/worker` | Reclama `queue` con `FOR UPDATE SKIP LOCKED`. Riesgo: locks huérfanos si el worker crashea. | El stub cierra el ciclo en `_handle_execution` (status=`succeeded`, borra fila de queue). El proyecto cliente extiende con timeouts y reintentos. |
| `dashboard/` | Página estática + un botón shadcn. | UI placeholder. NextAuth + provider real entran en v0.2.0. |
| `agent/services/clients/` | Vacío. Cuando el proyecto añada clientes externos (CRM, billing), pueden filtrar credenciales o PII si no se usa el patrón "single-centralised-client". | Patrón documentado en `docs/02_ARQUITECTURA.md`. PII redaction vía `loang_toolkit.PiiRedactor`. |
| `loang_toolkit` (dep pinned) | Hereda sus mitigaciones: identifier safety en SQL, redacción PII española, circuit breaker de tokens, prompt loading con front-matter validado. | Pinned a `v0.1.2`. |

## Manejo de secretos

Los secretos están enumerados en `.env.example`; ninguno tiene valor real en repo:

| Variable | Uso | Cuándo es obligatoria |
|---|---|---|
| `OPENROUTER_API_KEY` | Llamadas LLM vía `loang_toolkit.OpenRouterClient`. | En cuanto el agente haga una llamada real. |
| `DATABASE_URL` | Conexión a Postgres. | Siempre (incluso para `make migrate`). |
| `FERNET_KEY` | Cifrado en reposo de credenciales en BD. | Cuando el proyecto guarde credenciales del cliente final. Genera con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. |
| `NEXTAUTH_SECRET` | Firma de sesiones del dashboard. | Cuando NextAuth aterrice en v0.2.0; entretanto el dashboard es estático. |
| `LOANG_TOOLKIT_TOKEN` | Auth a `LoangIA/loang-toolkit` (privado) durante `pip install` en local Docker y CI. | Siempre que reconstruyas la imagen del agente o instales dependencias en CI. |

Reglas:

- **Nunca** se commitea `.env`, `.env.local`, ni similares (`.gitignore` raíz los excluye).
- En CI se inyectan vía `secrets.<NAME>` de GitHub Actions.
- En Docker, `LOANG_TOOLKIT_TOKEN` viaja como **BuildKit secret** (`docker-compose.yml secrets:` + `Dockerfile RUN --mount=type=secret,...`). No queda en capas de imagen.
- El logger JSON de `agent/_logging.py` reenvía cualquier campo `extra` que el caller añada al `LogRecord`. Si un proyecto cliente añade un secreto a `extra`, esa fuga es del proyecto, no del template — pero merece la pena auditar invocaciones a `_LOGGER.info(..., extra={...})` antes de release.

## Datos PII en pruebas y ejemplos

- `agent/src/agent/examples/_example.json` y los placeholders en `context/` y `prompts/` no contienen datos reales.
- Cuando el proyecto cliente cree golden cases con datos reales, anonimizarlos antes (preferiblemente con `loang_toolkit.PiiRedactor`) antes de commitearlos.

## Checklist de release (Fase 1 del proyecto cliente)

Antes del primer tag estable del proyecto que clonó este template:

- [ ] `make lint`, `make types`, `make test` verdes.
- [ ] `make verify-template-cleanup` sin pendientes (sale con exit 0).
- [ ] Ningún `print()` ni log con `api_key` / `FERNET_KEY` / sesión auth.
- [ ] `git ls-files | grep -Ei '\.env(\.local)?$'` vacío.
- [ ] `LOANG_TOOLKIT_TOKEN` rotado a service account (`LoangIA-bot`) si el proyecto va a CI compartido — no usar PAT personal.
- [ ] `docs/00_DECISIONES.md` con ADRs del proyecto (no solo los heredados del template).
- [ ] Cualquier desviación del stack del playbook documentada con ADR del proyecto.
- [ ] `docs/SECURITY.md` extendido con riesgos específicos del dominio del proyecto.

## Dependencias

Stack pinned con techos major (ver `agent/pyproject.toml` y `dashboard/package.json`). Cualquier subida major requiere ADR — del playbook si afecta al estándar, del proyecto si solo afecta a ese repo.

Avisos de seguridad de `httpx`, `pydantic`, `fastapi`, `langgraph`, `psycopg`, `next`, `eslint` se revisan trimestralmente.

## Historial

| Fecha | Versión | Notas |
|---|---|---|
| 2026-04-29 | v0.1.0 | Release inicial del template. Sin vulnerabilidades conocidas. |
| 2026-04-29 | v0.1.1 | Patch tras auditoría externa: BuildKit secret para `LOANG_TOOLKIT_TOKEN`, deps con techos major, `verify-template-cleanup` ahora es gate, este `SECURITY.md` añadido. |
