"""Request schemas for the Artifact API."""

import uuid

from pydantic import BaseModel, Field

from app.modules.artifact.domain.models import ArtifactStatus, ArtifactType


class CreateArtifactRequest(BaseModel):
    """Payload for creating a new artifact."""

    artifact_type: ArtifactType
    version: int = Field(default=1, ge=1)
    payload: dict = Field(default_factory=dict)
    execution_id: uuid.UUID | None = None


class UpdateArtifactRequest(BaseModel):
    """Payload for updating an existing artifact."""

    status: ArtifactStatus | None = None
    payload: dict | None = None
