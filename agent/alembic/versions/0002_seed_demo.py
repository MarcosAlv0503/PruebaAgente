"""Seed: insert demo customer for the Sprint 4 dashboard demo.

Run ``make migrate`` (or ``alembic upgrade head``) after ``make up`` to apply.

Revision ID: 0002_seed_demo
Revises: 0001_initial
Create Date: 2026-05-12 12:00:00 UTC
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_seed_demo"
down_revision: str | None = "0001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_DEMO_ID = "00000000-0000-0000-0000-000000000001"
_DEMO_NAME = "Tienda Demo"


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO customers (id, name, external_ref)
        VALUES ('{_DEMO_ID}', '{_DEMO_NAME}', 'demo')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM customers WHERE id = '{_DEMO_ID}';")
