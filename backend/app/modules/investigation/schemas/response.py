"""Response schemas for the Investigation API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.investigation.domain.models import InvestigationStatus


class InvestigationResponse(BaseModel):
    """Public representation of an investigation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    topic: str
    status: InvestigationStatus
    paper_limit: int
    created_at: datetime
    updated_at: datetime
    metadata: dict | None = Field(
        default=None,
        validation_alias="_metadata",
    )
