"""add extracted_knowledge table

Revision ID: 5f1b6d843b22
Revises: 5f1b6d843b21
Create Date: 2026-06-28 17:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "5f1b6d843b22"
down_revision: str | None = "5f1b6d843b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extracted_knowledge",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("execution_id", UUID(as_uuid=True), sa.ForeignKey("executions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("paper_title", sa.String(500), nullable=False),
        sa.Column("research_questions", JSONB, default=list, nullable=False),
        sa.Column("key_findings", JSONB, default=list, nullable=False),
        sa.Column("methodology", sa.Text, nullable=True),
        sa.Column("limitations", JSONB, default=list, nullable=False),
        sa.Column("key_contributions", JSONB, default=list, nullable=False),
        sa.Column("relevant_techniques", JSONB, default=list, nullable=False),
        sa.Column("cited_works", JSONB, default=list, nullable=False),
        sa.Column("future_work", JSONB, default=list, nullable=False),
        sa.Column("summary", sa.Text, default="", nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("extracted_knowledge")
