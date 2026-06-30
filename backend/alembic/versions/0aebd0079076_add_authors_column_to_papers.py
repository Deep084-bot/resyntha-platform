"""add authors column to papers

Revision ID: 0aebd0079076
Revises: 5f1b6d843b24
Create Date: 2026-06-30 23:35:55.359224
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "0aebd0079076"
down_revision: str | None = "5f1b6d843b24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("authors", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("papers", "authors")
