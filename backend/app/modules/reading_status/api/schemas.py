"""Paper reading status API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ReadingStatusSetRequest(BaseModel):
    status: str  # "unread", "reading", "completed", "skipped"


class ReadingStatusResponse(BaseModel):
    investigation_id: uuid.UUID
    paper_id: uuid.UUID
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}
