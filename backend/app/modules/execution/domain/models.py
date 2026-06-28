"""Execution ORM model and status enum.

An ``Execution`` represents a single pipeline run against an
investigation.  Artifacts and timeline events produced during the
run reference the execution that created them.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExecutionStatus(str, Enum):
    """Lifecycle states for an execution."""

    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Execution(Base):
    """A single pipeline execution run."""

    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        SAEnum(
            ExecutionStatus,
            name="execution_status",
            create_constraint=True,
        ),
        default=ExecutionStatus.PENDING,
        nullable=False,
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
