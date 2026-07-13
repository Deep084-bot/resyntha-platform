"""add copilot_conversations and copilot_messages tables

Revision ID: 0aebd0079077
Revises: 0aebd0079076
Create Date: 2026-07-01 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0aebd0079077"
down_revision: str | None = "0aebd0079076"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilot_conversations",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "investigation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "copilot_messages",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "conversation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_index(
        "ix_copilot_messages_conversation_id",
        "copilot_messages",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_copilot_messages_conversation_id", table_name="copilot_messages")
    op.drop_table("copilot_messages")
    op.drop_table("copilot_conversations")
