# Base de datos

PostgreSQL 16. Migraciones con Alembic en [`agent/alembic/`](../agent/alembic/). Schema base v0.1.0 con 4 tablas (de las 7 que define el playbook §13.16); `issues`, `human_tasks` y `audit_log` deferidas a v0.2.0 (ADR-002).

## Tablas v0.1.0

### `customers`

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    external_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Cada cliente final del proyecto. `external_ref` correla con el sistema upstream (CRM, billing).

### `executions`

```sql
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    external_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending','running','succeeded','failed','cancelled')),
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (customer_id, external_id)
);
```

Una fila por ejecución del agente. `UNIQUE(customer_id, external_id)` da idempotencia: un webhook que se reintenta con el mismo `external_id` no genera doble ejecución.

### `agent_usage`

```sql
CREATE TABLE agent_usage (
    id BIGSERIAL PRIMARY KEY,
    execution_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    duration_s DOUBLE PRECISION NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Una fila por llamada al LLM. Persistida por `loang_toolkit.TokenTracker`. Un `execution_id` puede tener N filas (una por fase con LLM).

### `queue`

```sql
CREATE TABLE queue (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    enqueued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_at TIMESTAMPTZ,
    locked_by TEXT,
    attempts INTEGER NOT NULL DEFAULT 0
);
```

Cola simple read-from-here. El worker reclama con `SELECT ... FOR UPDATE SKIP LOCKED` para soportar N workers en paralelo sin colisiones.

## Migraciones

```bash
make migrate          # aplica todas las pendientes
make migrate-down     # revierte la última
```

### Crear una migración nueva

```bash
cd agent
.venv/bin/alembic revision -m "add issues table"
```

Edita `agent/alembic/versions/<rev>_add_issues_table.py` y rellena `upgrade()` / `downgrade()`. Convención: SQL puro vía `op.execute(...)`, no SQLAlchemy ORM (el agente no usa ORM).

### Reglas

- Toda columna nueva nullable o con DEFAULT, así la migración no bloquea producción.
- `DROP TABLE` solo en migraciones que tengan `downgrade()` reversible (raro — normalmente preferimos depreciar).
- Cambios de `CHECK` constraint van en migración propia, no junto a otros cambios.
- El `external_id` de cualquier nueva tabla debe respetar `UNIQUE(customer_id, external_id)` para mantener idempotencia.

## Convenciones generales

- Identificadores en inglés (ADR-003): tablas, columnas, constraints, índices.
- Estados en inglés (`pending`, `running`, `succeeded`, `failed`, `cancelled`).
- Severidades en inglés (`info`, `warning`, `error`, `critical`) cuando aterrice `audit_log`.
- Timestamps siempre `TIMESTAMPTZ` con `now()` por defecto.
- IDs de entidades de dominio: UUID v4. IDs de eventos/queue: `BIGSERIAL`.
