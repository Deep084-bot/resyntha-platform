"""add execution_stages table and metadata column to executions

Revision ID: 5f1b6d843b21
Revises: d4bc8ca984b8
Create Date: 2026-06-28 16:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5f1b6d843b21"
down_revision: Union[str, None] = "d4bc8ca984b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add metadata JSONB column to executions
    op.add_column(
        "executions",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Create execution_stages table
    op.create_table(
        "execution_stages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column(
            "stage_name", sa.String(length=100), nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "COMPLETED",
                "FAILED",
                "SKIPPED",
                name="execution_stage_status",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            "completed_at", sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["executions.id"],
            name=op.f("fk_execution_stages_execution_id_executions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execution_stages")),
    )
    op.create_index(
        op.f("ix_execution_stages_execution_id"),
        "execution_stages",
        ["execution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_execution_stages_execution_id"),
        table_name="execution_stages",
    )
    op.drop_table("execution_stages")
    op.drop_column("executions", "metadata")
    op.execute("DROP TYPE IF EXISTS execution_stage_status")
