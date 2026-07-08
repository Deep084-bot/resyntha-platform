"""add chunk_embeddings table with pgvector support

Revision ID: 5f1b6d843b27
Revises: 5f1b6d843b26
Create Date: 2026-07-08 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "5f1b6d843b27"
down_revision: str | None = "5f1b6d843b26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "chunk_embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_id", UUID(as_uuid=True), nullable=True),
        sa.Column("paper_id", UUID(as_uuid=True), nullable=True),
        sa.Column("section", sa.String(100), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("artifact_version", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index(
        "ix_chunk_embeddings_investigation",
        "chunk_embeddings",
        ["investigation_id"],
    )

    op.create_index(
        "ix_chunk_embeddings_embedding",
        "chunk_embeddings",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_chunk_embeddings_embedding", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_investigation", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
    # Do NOT drop the vector extension in downgrade (may be used elsewhere)
