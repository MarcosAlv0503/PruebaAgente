# RUNBOOK — operativa diaria

Procedimientos paso a paso para operar el agente. Cuando algo se rompe, empieza por aquí.

## Pendientes post-clone (TODO loang-template)

Antes de declarar el proyecto en producción:

- [ ] Resolver todos los `TODO loang-template:` (`make verify-template-cleanup`).
- [ ] Editar `CLAUDE.md` raíz: rellenar el Top N anti-patrones del proyecto.
- [ ] Editar `docs/01_PROYECTO.md`: cliente, problema, capacidades × modo, volumetría, hitos.
- [ ] Editar `agent/src/agent/context/01-mision.md` con la misión real.
- [ ] Borrar lo que no se use (ej. `dashboard/` si es batch puro).
- [ ] Renombrar `loang-template` → `loang-<proyecto>` (`rg "loang-template" .`).
- [ ] **Branch protection** en `main`: requiere plan **Team** o superior en `LoangIA` (la org está en Free hasta el upgrade previsto en mayo de 2026; Free no expone branch protection en repos privados). Una vez en Team:

  ```bash
  gh api -X PUT /repos/LoangIA/loang-<proyecto>/branches/main/protection \
    -F required_status_checks.strict=true \
    -F 'required_status_checks.contexts[]=agent (Python)' \
    -F 'required_status_checks.contexts[]=dashboard (Next.js)' \
    -F enforce_admins=false \
    -F required_pull_request_reviews.required_approving_review_count=1 \
    -F restrictions= \
    -F allow_force_pushes=false \
    -F allow_deletions=false
  ```

## Tests rotos en CI pero verdes en local

1. Reproduce con la versión exacta de Python/Node de CI: `python3.13` y `node 20.x`.
2. Si pasa local pero no en CI, revisa caché de pip/npm — usa `actions/cache` correctamente, no fíes de versions ranges.
3. Si el fallo es el `pip install` de `loang-toolkit`, comprueba `LOANG_TOOLKIT_TOKEN` en secrets del repo.

## Migración Alembic falla en producción

```bash
flyctl ssh console -a <agent-app>
alembic current   # qué revisión está aplicada
alembic history   # qué hay disponible
```

Si la cabeza local diverge de la cabeza de producción:

1. **No** fuerces `alembic stamp` — pierdes la auditoría.
2. Crea una migración merge: `alembic merge -m "merge heads" <head1> <head2>`.
3. PR con la migración merge antes de aplicar.

## Cola atascada (worker no avanza)

```bash
# Ver entradas con lock antiguo
docker compose exec db psql -U loang -d loang -c \
  "SELECT id, execution_id, locked_at, locked_by FROM queue WHERE locked_at IS NOT NULL ORDER BY locked_at;"

# Liberar locks de un worker muerto
docker compose exec db psql -U loang -d loang -c \
  "UPDATE queue SET locked_at = NULL, locked_by = NULL WHERE locked_by = '<worker-name>';"
```

Causa común: worker crasheó dejando el lock. v0.1.0 no tiene timeout automático — TODO `loang-template:` añadirlo.

## Rotar PAT de `loang-toolkit`

1. Admin genera nuevo fine-grained PAT en `LoangIA-bot` con scope `Contents: read` sobre `LoangIA/loang-toolkit`.
2. Actualiza secret `LOANG_TOOLKIT_TOKEN` en GitHub Actions.
3. Re-corre el último workflow para verificar.
4. Revoca el viejo en GitHub UI.

## Subir versión del agente

```bash
# 1. Bumpea agent/pyproject.toml [project].version
# 2. Anota cambios en agent/src/agent/roadmap/changelog.md
git add -A
git commit -m "chore: agent 0.X.Y"
gh pr create --title "chore: agent 0.X.Y" --fill
# tras merge:
git checkout main && git pull
git tag agent-v0.X.Y && git push origin agent-v0.X.Y
```

(El template no auto-publica releases del agente — el agente vive dentro del proyecto cliente. Esto es para uso interno del proyecto.)

## Subir versión del template

Cuando este repo (el template) cambia:

1. Bump `package.json` y `agent/pyproject.toml` si aplica.
2. Anota cambios significativos en `docs/00_DECISIONES.md` (ADR-N nuevo si rompe).
3. Tag `v0.X.Y`. Proyectos clonados **no** se actualizan automáticamente — cada uno decide si cherry-pickea.

## Reportar incidente

1. Issue en `LoangIA/loang-<proyecto>` con label `incident`.
2. Slack al canal `#loang-ia-incidentes` con rango horario afectado y métricas.
3. Si afecta a coste OpenRouter: revisar `agent_usage` de las últimas 24h con `SELECT model, SUM(cost_usd), COUNT(*) FROM agent_usage WHERE created_at > now() - interval '24 hours' GROUP BY 1`.
4. Si causa raíz es bug del toolkit: abre issue en `LoangIA/loang-toolkit`, no en este repo.
