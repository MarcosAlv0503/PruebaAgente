"""Add thread_id to executions for multi-turn conversation tracking.

Revision ID: 0003_thread_id
Revises: 0002_seed_demo
Create Date: 2026-05-13 00:00:00 UTC
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_thread_id"
down_revision: str | None = "0002_seed_demo"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE executions
            ADD COLUMN IF NOT EXISTS thread_id UUID;
        CREATE INDEX IF NOT EXISTS idx_executions_thread_id
            ON executions (thread_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_executions_thread_id;
        ALTER TABLE executions DROP COLUMN IF EXISTS thread_id;
        """
    )
