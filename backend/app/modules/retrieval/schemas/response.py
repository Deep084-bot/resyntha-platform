"""Response schemas for the Retrieval API."""

import uuid

from pydantic import BaseModel, Field


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


class RetrieveResponse(BaseModel):
    """Result returned by the retrieval workflow."""

    investigation_id: uuid.UUID
    artifact_id: uuid.UUID
    paper_count: int
