"""Response schemas for the Retrieval API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaperResponse(BaseModel):
    """Public representation of a retrieved paper after ranking."""

    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    citation_count: int | None = None
    source: str = ""
    score: float = 0.0


class PersistedPaperResponse(BaseModel):
    """Public representation of a persisted paper with investigation metadata.

    ``id`` through ``updated_at`` come from the ``Paper`` ORM model.
    ``source`` comes from ``PaperSource`` and ``score`` comes from
    ``InvestigationPaper`` — both are populated manually in the API
    endpoint.
    """

    id: uuid.UUID
    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None
    venue: str | None = None
    year: int | None = None
    citation_count: int | None = None
    url: str | None = None
    source: str = ""
    score: float = 0.0
    created_at: datetime
    updated_at: datetime


class RetrieveResponse(BaseModel):
    """Result returned by the retrieval workflow."""

    investigation_id: uuid.UUID
    artifact_id: uuid.UUID
    paper_count: int


class RetrievalAcceptedResponse(BaseModel):
    """Returned after attempting to enqueue a retrieval job."""

    execution_id: uuid.UUID
    status: str = "pending"
    message: str | None = None
    queue_position: int | None = None
