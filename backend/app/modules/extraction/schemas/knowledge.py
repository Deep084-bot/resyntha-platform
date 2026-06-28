"""API schemas for extracted knowledge responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtractedKnowledgeResponse(BaseModel):
    """Single extracted knowledge record returned via API."""

    id: uuid.UUID
    investigation_id: uuid.UUID
    paper_id: uuid.UUID
    execution_id: uuid.UUID | None
    paper_title: str
    research_questions: list[str]
    key_findings: list[str]
    methodology: str | None
    limitations: list[str]
    key_contributions: list[str]
    relevant_techniques: list[str]
    cited_works: list[str]
    future_work: list[str]
    summary: str
    model_used: str
    tokens_used: int | None
    confidence_score: float | None
    created_at: datetime


class ExtractedKnowledgeListResponse(BaseModel):
    """List wrapper for extracted knowledge records."""

    items: list[ExtractedKnowledgeResponse]
