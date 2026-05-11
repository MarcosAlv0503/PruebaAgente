"""Initial schema: customers, executions, agent_usage, queue.

Subset of Playbook Loang §13.16 sufficient for the v0.1.0 template skeleton.
``issues``, ``human_tasks`` and ``audit_log`` are deferred to v0.2.0 once a
client project surfaces real requirements for them.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29 12:00:00 UTC
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
        """
    )
    op.execute(
        """
        CREATE TABLE customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            external_ref TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
            external_id TEXT,
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')
            ),
            input JSONB NOT NULL,
            output JSONB,
            error TEXT,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (customer_id, external_id)
        );
        CREATE INDEX executions_status_idx ON executions (status);
        CREATE INDEX executions_customer_idx ON executions (customer_id, created_at DESC);
        """
    )
    op.execute(
        """
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
        CREATE INDEX agent_usage_execution_idx ON agent_usage (execution_id);
        CREATE INDEX agent_usage_created_at_idx ON agent_usage (created_at DESC);
        """
    )
    op.execute(
        """
        CREATE TABLE queue (
            id BIGSERIAL PRIMARY KEY,
            execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
            enqueued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            locked_at TIMESTAMPTZ,
            locked_by TEXT,
            attempts INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX queue_unlocked_idx ON queue (enqueued_at) WHERE locked_at IS NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS queue;")
    op.execute("DROP TABLE IF EXISTS agent_usage;")
    op.execute("DROP TABLE IF EXISTS executions;")
    op.execute("DROP TABLE IF EXISTS customers;")
