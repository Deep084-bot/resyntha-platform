"""add rich extraction fields (authors, institutions, datasets, technologies, metrics, domains, keywords, paper_type, funding)

Revision ID: 5f1b6d843b26
Revises: 5f1b6d843b25
Create Date: 2026-07-08 20:50:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "5f1b6d843b26"
down_revision: str | None = "5f1b6d843b25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("extracted_knowledge", sa.Column("authors", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("institutions", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("datasets_used", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("technologies", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("evaluation_metrics", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("research_domains", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("keywords", JSONB, default=list, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("extracted_knowledge", sa.Column("paper_type", sa.String(100), nullable=True))
    op.add_column("extracted_knowledge", sa.Column("funding", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("extracted_knowledge", "funding")
    op.drop_column("extracted_knowledge", "paper_type")
    op.drop_column("extracted_knowledge", "keywords")
    op.drop_column("extracted_knowledge", "research_domains")
    op.drop_column("extracted_knowledge", "evaluation_metrics")
    op.drop_column("extracted_knowledge", "technologies")
    op.drop_column("extracted_knowledge", "datasets_used")
    op.drop_column("extracted_knowledge", "institutions")
    op.drop_column("extracted_knowledge", "authors")
