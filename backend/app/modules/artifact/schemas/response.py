"""Response schemas for the Artifact API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.artifact.domain.models import ArtifactStatus, ArtifactType


class ArtifactResponse(BaseModel):
    """Public representation of an artifact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    investigation_id: uuid.UUID
    execution_id: uuid.UUID | None = None
    artifact_type: ArtifactType
    version: int
    status: ArtifactStatus
    payload: dict | None
    created_at: datetime
    updated_at: datetime
