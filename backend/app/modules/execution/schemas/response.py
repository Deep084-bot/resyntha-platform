"""Response schemas for the Execution API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.execution.domain.models import ExecutionStatus


class ExecutionResponse(BaseModel):
    """Public representation of an execution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    investigation_id: uuid.UUID
    status: ExecutionStatus
    trigger: str
    created_by: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
