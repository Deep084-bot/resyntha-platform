"""Retrieval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.execution.schemas.request import CreateExecutionRequest
from app.modules.execution.service.service import ExecutionService
from app.modules.investigation.service.service import InvestigationService
from app.modules.paper.domain.models import InvestigationPaper
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

    execution_service = ExecutionService(db)

    # Prevent duplicate concurrent retrievals.
    if execution_service.has_active_execution(investigation_id):
        executions = execution_service.list_executions(investigation_id)
        existing = executions[0] if executions else None
        logger.warning(
            "retrieval_already_running",
            investigation_id=str(investigation_id),
            existing_execution_id=str(existing.id) if existing else None,
        )
        return RetrievalAcceptedResponse(
            execution_id=existing.id if existing else uuid.uuid4(),
            status="already_running",
            message="A retrieval is already running for this investigation.",
        )

    # Create execution in PENDING — worker transitions to RUNNING.
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
    """Return all papers attached to an investigation with source and score."""
    repo = PaperRepository(db)
    papers = repo.list_by_investigation(investigation_id)

    from app.modules.paper.domain.models import PaperSource

    paper_ids = [p.id for p in papers]
    # Batch-load sources for all papers.
    source_rows = (
        db.execute(
            select(PaperSource).where(PaperSource.paper_id.in_(paper_ids)),
        )
        .scalars()
        .all()
    )
    source_map: dict[uuid.UUID, str] = {}
    for src in source_rows:
        if src.paper_id not in source_map:
            source_map[src.paper_id] = src.provider

    # Build a lookup of investigation-specific scores.
    inv_links = {
        lp.paper_id: lp
        for lp in db.scalars(
            select(InvestigationPaper).where(
                InvestigationPaper.investigation_id == investigation_id,
            ),
        ).all()
    }

    results: list[PersistedPaperResponse] = []
    for p in papers:
        link = inv_links.get(p.id)
        results.append(
            PersistedPaperResponse(
                id=p.id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors if p.authors is not None else [],
                doi=p.doi,
                venue=p.venue,
                year=p.year,
                citation_count=p.citation_count,
                url=p.url,
                source=source_map.get(p.id, ""),
                score=link.relevance_score if link is not None else 0.0,
                created_at=p.created_at,
                updated_at=p.updated_at,
            ),
        )
    return results
