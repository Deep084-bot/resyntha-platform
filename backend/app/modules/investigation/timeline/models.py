"""Timeline ORM model and stage/status enums.

An ``InvestigationTimeline`` row records a single checkpoint in an
investigation's lifecycle.  The sequence of these rows forms an
auditable history.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TimelineStage(StrEnum):
    """Stages an investigation passes through during its lifecycle."""

    CREATED = "created"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TimelineStatus(StrEnum):
    """Outcome of a timeline stage."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    RUNNING = "running"


class InvestigationTimeline(Base):
    """A single event in an investigation's history."""

    __tablename__ = "investigation_timeline"

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
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stage: Mapped[TimelineStage] = mapped_column(
        SAEnum(TimelineStage, name="timeline_stage"),
        nullable=False,
    )
    status: Mapped[TimelineStatus] = mapped_column(
        SAEnum(TimelineStatus, name="timeline_status"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict, nullable=True)
