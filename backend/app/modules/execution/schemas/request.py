"""Request schemas for the Execution API."""

from pydantic import BaseModel, Field

from app.modules.execution.domain.models import ExecutionStatus


class CreateExecutionRequest(BaseModel):
    """Payload for creating a new execution."""

    trigger: str = Field(..., min_length=1, max_length=50)
    created_by: str | None = Field(default=None, max_length=255)


class UpdateExecutionRequest(BaseModel):
    """Payload for updating an existing execution."""

    status: ExecutionStatus | None = None
