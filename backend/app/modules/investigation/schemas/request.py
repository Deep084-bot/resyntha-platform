"""Request schemas for the Investigation API."""

from pydantic import BaseModel, Field


class CreateInvestigationRequest(BaseModel):
    """Payload for creating a new investigation."""

    title: str = Field(..., min_length=1, max_length=255)
    topic: str = Field(..., min_length=1)
    paper_limit: int = Field(default=10, ge=1, le=100)
