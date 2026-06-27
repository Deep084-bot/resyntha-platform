"""Request schemas for the Retrieval API."""

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    """Payload for triggering a paper retrieval."""

    query: str = Field(..., min_length=1)
    paper_limit: int = Field(default=10, ge=1, le=100)
