"""add research_gap_report artifact type value

Revision ID: 5f1b6d843b24
Revises: 5f1b6d843b23
Create Date: 2026-06-28 18:20:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5f1b6d843b24"
down_revision: str | None = "5f1b6d843b23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE artifact_type ADD VALUE 'research_gap_report'")


def downgrade() -> None:
    pass
