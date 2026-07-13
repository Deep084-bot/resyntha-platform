"""Notes and highlights ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Note(Base):
    """A user note or highlight attached to an investigation.

    Notes support markdown content and optional tags.
    Highlights are notes with a ``source_type`` and ``source_id``
    referencing the original content (copilot response, graph node,
    paper summary, research gap).
    """

    __tablename__ = "notes"

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
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Highlight source (null for free-form notes)
    source_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_context: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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


class NoteLink(Base):
    """A reference from a note to an external entity.

    Notes can reference papers, graph nodes, Copilot answers,
    and artifacts to maintain relationships in the database.
    """

    __tablename__ = "note_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    target_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
