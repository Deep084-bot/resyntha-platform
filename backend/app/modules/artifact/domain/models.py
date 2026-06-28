"""Artifact ORM model and type/status enums.

An ``Artifact`` represents a versioned output produced during an
investigation — for example a paper collection, a comparison matrix,
or a final report.  The ``payload`` column stores the actual content
as free-form JSONB.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ArtifactType(str, Enum):
    """Known artifact kinds that the platform can produce."""

    EXECUTION_PLAN = "execution_plan"
    PAPER_COLLECTION = "paper_collection"
    VALIDATED_COLLECTION = "validated_collection"
    KNOWLEDGE_PACKAGE = "knowledge_package"
    RESEARCH_LANDSCAPE = "research_landscape"
    RESEARCH_GAP_REPORT = "research_gap_report"
    COMPARISON_MATRIX = "comparison_matrix"
    TREND_REPORT = "trend_report"
    OPPORTUNITY_REPORT = "opportunity_report"
    RESEARCH_IDEAS = "research_ideas"
    FINAL_REPORT = "final_report"


class ArtifactStatus(str, Enum):
    """Lifecycle states for an artifact."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class Artifact(Base):
    """A versioned output produced during an investigation."""

    __tablename__ = "artifacts"

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
    artifact_type: Mapped[ArtifactType] = mapped_column(
        SAEnum(ArtifactType, name="artifact_type"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[ArtifactStatus] = mapped_column(
        SAEnum(ArtifactStatus, name="artifact_status"),
        default=ArtifactStatus.PENDING,
        nullable=False,
    )
    payload: Mapped[dict | None] = mapped_column(
        JSONB, default=dict, nullable=True
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
