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
    """Public representation of a persisted paper (ORM model)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    venue: str | None = None
    year: int | None = None
    citation_count: int | None = None
    url: str | None = None
    created_at: datetime
    updated_at: datetime


class RetrieveResponse(BaseModel):
    """Result returned by the retrieval workflow."""

    investigation_id: uuid.UUID
    artifact_id: uuid.UUID
    paper_count: int
