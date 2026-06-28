"""Pydantic schemas for the Timeline sub-module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.investigation.timeline.models import (
    TimelineStage,
    TimelineStatus,
)


class TimelineEventResponse(BaseModel):
    """Public representation of a single timeline event."""

    model_config = ConfigDict(from_attributes=True)

    stage: TimelineStage
    status: TimelineStatus
    message: str
    execution_id: uuid.UUID | None = None
    created_at: datetime
