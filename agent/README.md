# `agent/` — backend del template

FastAPI + LangGraph + Postgres + Alembic. Importa [`loang-toolkit`](https://github.com/LoangIA/loang-toolkit) con tag pinned para tracking de tokens, redacción de PII, cliente OpenRouter y carga de prompts versionados.

Todo el código real del agente vive aquí. La estructura sigue las plantillas §13.6 / §13.20 del Playbook Loang.

Para arrancar el venv local:

```bash
cd agent
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

(`pip install` clonará `loang-toolkit` por HTTPS contra GitHub. Necesitas tu PAT configurado vía `gh auth setup-git`.)

Comandos del proyecto desde la raíz: `make test`, `make types`, `make lint`, `make migrate`, `make worker`, `make rn ID=<customer-id>`.
