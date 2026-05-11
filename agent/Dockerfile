# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for psycopg-binary, git for git+https deps.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

# Install the agent (and ``loang-toolkit`` from its private GitHub release).
# The token comes via a BuildKit secret named ``loang_toolkit_token``: it is
# only mounted for the duration of this RUN, never copied into a layer.
# Build with `DOCKER_BUILDKIT=1` and pass the secret either via
# `docker compose build` (see docker-compose.yml) or with
# `docker build --secret id=loang_toolkit_token,env=LOANG_TOOLKIT_TOKEN`.
RUN --mount=type=secret,id=loang_toolkit_token \
    set -e; \
    if [ -s /run/secrets/loang_toolkit_token ]; then \
        token="$(cat /run/secrets/loang_toolkit_token)"; \
        git config --global \
            url."https://x-access-token:${token}@github.com/".insteadOf \
            "https://github.com/"; \
    else \
        echo "WARNING: loang_toolkit_token secret missing — pip install of loang-toolkit will fail unless the dep resolves anonymously."; \
    fi; \
    pip install --upgrade pip && \
    pip install ".[dev]"; \
    git config --global --unset-all url."https://x-access-token:${token}@github.com/".insteadOf 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
