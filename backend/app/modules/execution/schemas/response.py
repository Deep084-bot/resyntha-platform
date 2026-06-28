"""Response schemas for the Execution API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.execution.domain.models import ExecutionStageStatus, ExecutionStatus


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


class ExecutionStageResponse(BaseModel):
    """Public representation of a single pipeline stage execution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    stage_name: str
    status: ExecutionStageStatus
    attempt: int
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    created_at: datetime
