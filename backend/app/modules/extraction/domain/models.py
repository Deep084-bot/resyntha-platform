"""Extraction ORM models.

``ExtractedKnowledge`` persists per-paper LLM extraction results so
they are queryable and reusable across investigations.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractedKnowledge(Base):
    """Structured knowledge extracted from a single paper via LLM."""

    __tablename__ = "extracted_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    paper_title: Mapped[str] = mapped_column(String(500), nullable=False)

    # ── Existing fields ───────────────────────────────────────────
    research_questions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    key_findings: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    key_contributions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    relevant_techniques: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    cited_works: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    future_work: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # ── New structured fields ─────────────────────────────────────
    authors: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    institutions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    datasets_used: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    technologies: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    evaluation_metrics: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    research_domains: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    keywords: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    paper_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    funding: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Provenance ────────────────────────────────────────────────
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
