"""Artifact CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.artifact.schemas.request import (
    CreateArtifactRequest,
    UpdateArtifactRequest,
)
from app.modules.artifact.schemas.response import (
    ArtifactResponse,
)
from app.modules.artifact.service.service import (
    ArtifactService,
)
from app.observability.logger import get_logger

router = APIRouter(tags=["artifacts"])
logger = get_logger(__name__)


def _get_service(db: Session = Depends(get_db)) -> ArtifactService:
    return ArtifactService(db)


@router.post(
    "/investigations/{investigation_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    investigation_id: uuid.UUID,
    body: CreateArtifactRequest,
    service: ArtifactService = Depends(_get_service),
) -> ArtifactResponse:
    """Create a new artifact linked to an investigation."""
    logger.info(
        "artifact_created",
        investigation_id=str(investigation_id),
        artifact_type=body.artifact_type.value,
    )
    return service.create_artifact(investigation_id, body)


@router.get(
    "/investigations/{investigation_id}/artifacts",
    response_model=list[ArtifactResponse],
)
async def list_artifacts(
    investigation_id: uuid.UUID,
    service: ArtifactService = Depends(_get_service),
) -> list[ArtifactResponse]:
    """Return all artifacts for an investigation."""
    logger.info("artifacts_listed", investigation_id=str(investigation_id))
    return list(service.list_artifacts(investigation_id))


@router.get(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def get_artifact(
    artifact_id: uuid.UUID,
    service: ArtifactService = Depends(_get_service),
) -> ArtifactResponse:
    """Return a single artifact by id."""
    artifact = service.get_artifact(artifact_id)
    if artifact is None:
        logger.warning("artifact_not_found", id=str(artifact_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("artifact_retrieved", id=str(artifact_id))
    return artifact


@router.patch(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def update_artifact(
    artifact_id: uuid.UUID,
    body: UpdateArtifactRequest,
    service: ArtifactService = Depends(_get_service),
) -> ArtifactResponse:
    """Update an artifact's status and/or payload."""
    artifact = service.update_artifact(artifact_id, body)
    if artifact is None:
        logger.warning("artifact_not_found", id=str(artifact_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("artifact_updated", id=str(artifact_id))
    return artifact
