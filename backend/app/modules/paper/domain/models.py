"""Paper ORM models and related persistence entities."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Paper(Base):
    """Globally unique paper identified by DOI or exact title."""

    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str] | None] = mapped_column(JSONB, default=list, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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


class PaperSource(Base):
    """Tracks which provider a paper was sourced from and its original identifier."""

    __tablename__ = "paper_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_identifier: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class InvestigationPaper(Base):
    """Many-to-many link between investigations and papers with ranking metadata."""

    __tablename__ = "investigation_papers"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
