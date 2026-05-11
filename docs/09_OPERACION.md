# Operación — local + deploy

## Arrancar local

```bash
cp .env.example .env
# Edita .env: OPENROUTER_API_KEY, FERNET_KEY, NEXTAUTH_SECRET y LOANG_TOOLKIT_TOKEN.
# Para LOANG_TOOLKIT_TOKEN, en local puedes usar `gh auth token` mientras no
# exista la cuenta de servicio LoangIA-bot.
echo "LOANG_TOOLKIT_TOKEN=$(gh auth token)" >> .env

make install-agent       # crea .venv (Python 3.13) e instala deps + loang-toolkit
make install-dashboard
make up                  # docker compose: db + agent + worker + dashboard
make migrate             # aplica schema base
```

`make up` exporta `LOANG_TOOLKIT_TOKEN` del entorno como secret BuildKit (ver `docker-compose.yml`); `agent/Dockerfile` lo monta solo durante el `pip install` y nunca lo copia a una capa de la imagen.

Dashboard: http://localhost:3000. Agent API: http://localhost:8000. Probar: `curl http://localhost:8000/health` debería devolver `{"status":"ok","db":"ok"}`.

## Lanzar trabajo

```bash
# Crear un customer manualmente (v0.1.0 no tiene endpoint para eso):
docker compose exec db psql -U loang -d loang -c \
  "INSERT INTO customers (id, name) VALUES ('00000000-0000-0000-0000-000000000001', 'Demo cliente');"

# Encolar una ejecución:
make rn ID=00000000-0000-0000-0000-000000000001

# Ver el log del worker:
docker compose logs -f worker
```

## Reintentar ejecución fallida

```bash
make rn-retry ID=<execution-uuid>
```

Eso re-encola la entrada existente; el worker la cogerá con `attempts = attempts + 1`.

## Pausar el bot

v0.1.0 stub:

```bash
make bot-pause   # stubeado; devuelve 404 hasta que el proyecto implemente la flag
```

TODO `loang-template:` cuando aterrice tabla `audit_log`, este endpoint persiste un row indicando "bot pausado por <user> a las <ts>" y el worker comprueba la flag antes de cada `_claim_one`.

## Configurar PAT para `pip install` de `loang-toolkit`

`loang-toolkit` está en repo privado de `LoangIA`. `pip install` necesita auth:

### Local (dev)

```bash
gh auth setup-git
```

Eso instala un credential helper que reusa tu PAT de `gh` para HTTPS. Luego `pip install` funciona.

### CI

GitHub Actions necesita un PAT con `repo` scope sobre `LoangIA/loang-toolkit`:

1. Admin de la org crea un fine-grained PAT desde `LoangIA-bot` (cuenta servicio) con acceso a `LoangIA/loang-toolkit` y permiso `Contents: read`.
2. Lo guarda como secret `LOANG_TOOLKIT_TOKEN` en el repo cliente.
3. El job de CI lo expone con `git config insteadOf` antes del `pip install` (ver [`.github/workflows/ci.yml`](../.github/workflows/ci.yml#L20-L31)).

## Deploy a Fly.io

**v0.1.0 no incluye `fly.toml` ni `deploy.yml`.** Diferido a v0.2.0 según ADR-002. Cuando el proyecto cliente esté listo:

```bash
flyctl launch --name loang-<proyecto> --region mad
flyctl secrets set OPENROUTER_API_KEY=... FERNET_KEY=... NEXTAUTH_SECRET=...
flyctl deploy
```

Y abre PR en este template para que `fly.toml` quede pre-cableado para los siguientes proyectos.

## Rotar secretos

| Secret | Cómo se rota | Qué se rompe mientras tanto |
|---|---|---|
| `OPENROUTER_API_KEY` | Generar nueva en OpenRouter UI, `flyctl secrets set OPENROUTER_API_KEY=...`, esperar redeploy. Revocar la vieja después. | Nada si lo haces en orden. |
| `FERNET_KEY` | **Coordinar.** Cualquier credencial cifrada en BD con la vieja deja de descifrarse. Procedimiento: añadir nueva como secundaria, recifrar todo, retirar la vieja. | Lecturas de credenciales descifradas. |
| `NEXTAUTH_SECRET` | `flyctl secrets set NEXTAUTH_SECRET=$(openssl rand -base64 32)`. | Sesiones activas se invalidan; usuarios re-loguean. |
| `LOANG_TOOLKIT_TOKEN` (CI) | Regenerar en GitHub UI, actualizar secret. | CI builds nuevos fallan hasta que se actualiza. |

## Backup / restore (Postgres en Fly.io)

```bash
# Backup manual:
flyctl postgres backup create -a <postgres-app>
flyctl postgres backup list -a <postgres-app>

# Restore:
flyctl postgres backup restore <backup-id> -a <postgres-app>
```

Backups automáticos diarios los gestiona Fly.io. Verifica retención según el plan que tenga el proyecto.
