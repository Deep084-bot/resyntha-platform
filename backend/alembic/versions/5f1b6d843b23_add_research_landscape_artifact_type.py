"""add research_landscape artifact type value

Revision ID: 5f1b6d843b23
Revises: 5f1b6d843b22
Create Date: 2026-06-28 17:45:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5f1b6d843b23"
down_revision: str | None = "5f1b6d843b22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE artifact_type ADD VALUE 'research_landscape'")


def downgrade() -> None:
    # PostgreSQL does not support removing a value from an enum.
    # This would require a more complex migration (create new type,
    # migrate columns, drop old type). For dev purposes the value
    # can safely remain unused.
    pass
