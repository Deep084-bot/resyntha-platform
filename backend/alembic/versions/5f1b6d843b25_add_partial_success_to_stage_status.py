"""add PARTIAL_SUCCESS to execution_stage_status enum

Revision ID: 5f1b6d843b25
Revises: 0aebd0079077
Create Date: 2026-07-02 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5f1b6d843b25"
down_revision: str | None = "0aebd0079077"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE execution_stage_status ADD VALUE 'PARTIAL_SUCCESS'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from a native ENUM.
    # A proper downgrade would require creating a new type without the
    # value, migrating all columns, and dropping the old type.
    # Since this is a new value only used by future pipeline runs, the
    # simplest safe downgrade is a no-op.
    pass
