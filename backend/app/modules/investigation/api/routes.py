"""Investigation CRUD and timeline endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.investigation.schemas.request import (
    CreateInvestigationRequest,
)
from app.modules.investigation.schemas.response import (
    InvestigationResponse,
)
from app.modules.investigation.service.service import (
    InvestigationService,
)
from app.modules.investigation.timeline.schemas import (
    TimelineEventResponse,
)
from app.observability.logger import get_logger

router = APIRouter(prefix="/investigations", tags=["investigations"])
logger = get_logger(__name__)


def _get_service(db: Session = Depends(get_db)) -> InvestigationService:
    return InvestigationService(db)


@router.post(
    "/",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_investigation(
    body: CreateInvestigationRequest,
    service: InvestigationService = Depends(_get_service),
) -> InvestigationResponse:
    """Create a new investigation."""
    logger.info("investigation_created", title=body.title)
    return service.create_investigation(body)


@router.get("/", response_model=list[InvestigationResponse])
async def list_investigations(
    skip: int = 0,
    limit: int = 100,
    service: InvestigationService = Depends(_get_service),
) -> list[InvestigationResponse]:
    """Return a paginated list of investigations."""
    logger.info("investigations_listed")
    return list(service.list_investigations(skip=skip, limit=limit))


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
)
async def get_investigation(
    investigation_id: uuid.UUID,
    service: InvestigationService = Depends(_get_service),
) -> InvestigationResponse:
    """Return a single investigation by id."""
    investigation = service.get_investigation(investigation_id)
    if investigation is None:
        logger.warning("investigation_not_found", id=str(investigation_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("investigation_retrieved", id=str(investigation_id))
    return investigation


@router.delete(
    "/{investigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_investigation(
    investigation_id: uuid.UUID,
    service: InvestigationService = Depends(_get_service),
) -> None:
    """Delete an investigation by id."""
    deleted = service.delete_investigation(investigation_id)
    if not deleted:
        logger.warning("investigation_not_found", id=str(investigation_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("investigation_deleted", id=str(investigation_id))


@router.get(
    "/{investigation_id}/timeline",
    response_model=list[TimelineEventResponse],
)
async def get_investigation_timeline(
    investigation_id: uuid.UUID,
    service: InvestigationService = Depends(_get_service),
) -> list[TimelineEventResponse]:
    """Return the timeline for an investigation."""
    timeline = service.get_timeline(investigation_id)
    logger.info("timeline_retrieved", id=str(investigation_id))
    return list(timeline)
