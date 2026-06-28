"""Retrieval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.execution.schemas.request import CreateExecutionRequest
from app.modules.execution.service.service import ExecutionService
from app.modules.investigation.service.service import InvestigationService
from app.modules.paper.repository.repository import PaperRepository
from app.modules.retrieval.schemas.request import RetrieveRequest
from app.modules.retrieval.schemas.response import (
    PersistedPaperResponse,
    RetrievalAcceptedResponse,
)
from app.observability.logger import get_logger
from app.workers.worker import enqueue_retrieval

router = APIRouter(tags=["retrieval"])
logger = get_logger(__name__)


@router.post(
    "/investigations/{investigation_id}/retrieve",
    response_model=RetrievalAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retrieve_papers(
    investigation_id: uuid.UUID,
    body: RetrieveRequest,
    db: Session = Depends(get_db),
) -> RetrievalAcceptedResponse:
    """Enqueue a retrieval pipeline job and return immediately.

    The actual work (searching providers, persisting papers, creating
    artifacts, recording timeline) runs in an ARQ background worker.
    Poll ``GET /investigations/{id}/executions`` to track progress.
    """
    logger.info(
        "retrieval_enqueuing",
        investigation_id=str(investigation_id),
        query=body.query,
    )

    investigation_service = InvestigationService(db)
    investigation = investigation_service.get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Create execution in PENDING — worker transitions to RUNNING.
    execution_service = ExecutionService(db)
    execution = execution_service.create_execution(
        investigation_id,
        CreateExecutionRequest(trigger="manual"),
    )

    await enqueue_retrieval(
        execution_id=str(execution.id),
        investigation_id=str(investigation_id),
        query=body.query,
        paper_limit=body.paper_limit,
    )

    logger.info(
        "retrieval_enqueued",
        execution_id=str(execution.id),
        investigation_id=str(investigation_id),
    )

    return RetrievalAcceptedResponse(
        execution_id=execution.id,
        status="pending",
    )


@router.get(
    "/investigations/{investigation_id}/papers",
    response_model=list[PersistedPaperResponse],
)
async def list_papers(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[PersistedPaperResponse]:
    """Return all papers attached to an investigation."""
    repo = PaperRepository(db)
    papers = repo.list_by_investigation(investigation_id)
    return [PersistedPaperResponse.model_validate(p) for p in papers]
