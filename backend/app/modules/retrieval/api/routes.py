"""Retrieval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.artifact.service.service import ArtifactService
from app.modules.execution.domain.models import ExecutionStatus
from app.modules.execution.schemas.request import (
    CreateExecutionRequest,
    UpdateExecutionRequest,
)
from app.modules.execution.service.service import ExecutionService
from app.modules.investigation.service.service import InvestigationService
from app.modules.investigation.timeline.models import TimelineStage, TimelineStatus
from app.modules.investigation.timeline.service import TimelineService
from app.modules.paper.repository.repository import PaperRepository
from app.modules.paper.service.service import PaperService
from app.modules.retrieval.schemas.request import RetrieveRequest
from app.modules.retrieval.schemas.response import (
    PersistedPaperResponse,
    RetrieveResponse,
)
from app.observability.logger import get_logger
from app.pipeline import PipelineContext, PipelineDefinition
from app.pipeline.stages import (
    ArtifactStage,
    PersistStage,
    RetrieveStage,
    TimelineStage,
)

router = APIRouter(tags=["retrieval"])
logger = get_logger(__name__)


@router.post(
    "/investigations/{investigation_id}/retrieve",
    response_model=RetrieveResponse,
    status_code=status.HTTP_201_CREATED,
)
async def retrieve_papers(
    investigation_id: uuid.UUID,
    body: RetrieveRequest,
    db: Session = Depends(get_db),
) -> RetrieveResponse:
    """Search for papers, persist them, create a paper-collection artifact,
    and record timeline events.

    Creates an Execution record to track the run and associates
    artifacts and timeline events with that execution.
    """
    logger.info(
        "retrieval_requested",
        investigation_id=str(investigation_id),
        query=body.query,
    )

    investigation_service = InvestigationService(db)
    investigation = investigation_service.get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Create and start execution
    execution_service = ExecutionService(db)
    execution = execution_service.create_execution(
        investigation_id,
        CreateExecutionRequest(trigger="manual"),
    )
    execution_service.update_execution(
        execution.id,
        UpdateExecutionRequest(status=ExecutionStatus.RUNNING),
    )

    timeline_service = TimelineService(db)
    timeline_service.record_event(
        investigation_id=investigation_id,
        execution_id=execution.id,
        stage=TimelineStage.RETRIEVING,
        status=TimelineStatus.RUNNING,
        message="Paper retrieval started",
    )

    context = PipelineContext(
        investigation_id=investigation_id,
        execution_id=execution.id,
    )
    context.set_metadata("query", body.query)
    context.set_metadata("paper_limit", body.paper_limit)
    context.set_metadata("timeline_stage", "retrieving")

    definition = PipelineDefinition(
        name="retrieve",
        stages=[
            RetrieveStage(),
            PersistStage(PaperService(db)),
            ArtifactStage(ArtifactService(db)),
            TimelineStage(TimelineService(db)),
        ],
    )

    final_context = await definition.run(context)

    if final_context.execution_state.get("failed_at"):
        timeline_service.record_event(
            investigation_id=investigation_id,
            execution_id=execution.id,
            stage=TimelineStage.RETRIEVING,
            status=TimelineStatus.FAILURE,
            message="Retrieval failed",
        )
        execution_service.update_execution(
            execution.id,
            UpdateExecutionRequest(status=ExecutionStatus.FAILED),
        )
        logger.error(
            "retrieval_failed",
            investigation_id=str(investigation_id),
            errors=final_context.errors,
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    execution_service.update_execution(
        execution.id,
        UpdateExecutionRequest(status=ExecutionStatus.COMPLETED),
    )

    artifact = final_context.get_artifact("artifact_response")
    paper_count = final_context.metrics.get("paper_count", 0)

    return RetrieveResponse(
        investigation_id=investigation_id,
        artifact_id=artifact.id,
        paper_count=paper_count,
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
