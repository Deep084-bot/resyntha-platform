"""Request schemas for the Artifact API."""

from pydantic import BaseModel, Field

from app.modules.artifact.domain.models import ArtifactStatus, ArtifactType


class CreateArtifactRequest(BaseModel):
    """Payload for creating a new artifact."""

    artifact_type: ArtifactType
    version: int = Field(default=1, ge=1)
    payload: dict = Field(default_factory=dict)


class UpdateArtifactRequest(BaseModel):
    """Payload for updating an existing artifact."""

    status: ArtifactStatus | None = None
    payload: dict | None = None
