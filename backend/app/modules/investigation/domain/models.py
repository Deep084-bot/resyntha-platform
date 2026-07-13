"""Investigation ORM model and status enum.

The ``Investigation`` table stores top-level research investigations.
All domain state lives here; no business logic or persistence
concerns leak into this file.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class InvestigationStatus(StrEnum):
    """Lifecycle states for an investigation."""

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


class Investigation(Base):
    """Represents a single research investigation."""

    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InvestigationStatus] = mapped_column(
        SAEnum(
            InvestigationStatus,
            name="investigation_status",
            create_constraint=True,
        ),
        default=InvestigationStatus.CREATED,
        nullable=False,
    )
    paper_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
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
    _metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict, nullable=True)
