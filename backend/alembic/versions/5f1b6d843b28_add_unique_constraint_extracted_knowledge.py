"""add unique constraint on (paper_id, execution_id) for dedup

Revision ID: 5f1b6d843b28
Revises: 5f1b6d843b27
Create Date: 2026-07-21 18:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5f1b6d843b28"
down_revision: str | None = "5f1b6d843b27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove duplicates first: keep the earliest row per (paper_id, execution_id)
    op.execute(
        """
        DELETE FROM extracted_knowledge a
            USING extracted_knowledge b
        WHERE a.id > b.id
          AND a.paper_id = b.paper_id
          AND a.execution_id IS NOT NULL
          AND b.execution_id IS NOT NULL
          AND a.execution_id = b.execution_id
        """
    )

    op.create_index(
        "ix_extracted_knowledge_paper_execution",
        "extracted_knowledge",
        ["paper_id", "execution_id"],
        unique=True,
        postgresql_where=op.text("execution_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_extracted_knowledge_paper_execution",
        table_name="extracted_knowledge",
        postgresql_where=op.text("execution_id IS NOT NULL"),
    )
