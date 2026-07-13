"""Artifact service.

Implements business rules around artifact creation, status updates,
and querying.  The service owns the transaction boundary and commits
after each write operation.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import (
    Artifact,
    ArtifactStatus,
)
from app.modules.artifact.repository.repository import (
    ArtifactRepository,
)
from app.modules.artifact.schemas.request import (
    CreateArtifactRequest,
    UpdateArtifactRequest,
)
from app.modules.artifact.schemas.response import (
    ArtifactResponse,
)


class ArtifactService:
    """Encapsulates artifact business logic."""

    def __init__(self, session: Session) -> None:
        self._repository = ArtifactRepository(session)
        self._session = session

    def create_artifact(
        self,
        investigation_id: uuid.UUID,
        request: CreateArtifactRequest,
        status: ArtifactStatus = ArtifactStatus.PENDING,
    ) -> ArtifactResponse:
        """Create a new artifact linked to an investigation and optionally an execution.

        Default status is ``PENDING``; callers that generate final
        content should pass ``ArtifactStatus.READY`` so the artifact
        is immediately visible in the UI.
        """
        artifact = Artifact(
            investigation_id=investigation_id,
            execution_id=request.execution_id,
            artifact_type=request.artifact_type,
            version=request.version,
            status=status,
            payload=request.payload,
        )
        saved = self._repository.create(artifact)
        self._session.commit()
        return ArtifactResponse.model_validate(saved)

    def update_artifact(
        self,
        artifact_id: uuid.UUID,
        request: UpdateArtifactRequest,
    ) -> ArtifactResponse | None:
        """Update an artifact's status and/or payload.

        Returns ``None`` when the artifact does not exist.
        """
        artifact = self._repository.get_by_id(artifact_id)
        if artifact is None:
            return None

        if request.status is not None:
            artifact.status = request.status
        if request.payload is not None:
            artifact.payload = request.payload

        updated = self._repository.update(artifact)
        self._session.commit()
        return ArtifactResponse.model_validate(updated)

    def get_artifact(self, artifact_id: uuid.UUID) -> ArtifactResponse | None:
        """Return an artifact by id, or ``None``."""
        artifact = self._repository.get_by_id(artifact_id)
        if artifact is None:
            return None
        return ArtifactResponse.model_validate(artifact)

    def list_artifacts(self, investigation_id: uuid.UUID) -> Sequence[ArtifactResponse]:
        """Return all artifacts for an investigation."""
        artifacts = self._repository.list_by_investigation(investigation_id)
        return [ArtifactResponse.model_validate(a) for a in artifacts]
