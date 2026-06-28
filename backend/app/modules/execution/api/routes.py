"""Execution CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.execution.schemas.request import (
    CreateExecutionRequest,
    UpdateExecutionRequest,
)
from app.modules.execution.schemas.response import (
    ExecutionResponse,
    ExecutionStageResponse,
)
from app.modules.execution.service.service import (
    ExecutionService,
    ExecutionStageService,
)
from app.observability.logger import get_logger

router = APIRouter(tags=["executions"])
logger = get_logger(__name__)


def _get_service(db: Session = Depends(get_db)) -> ExecutionService:
    return ExecutionService(db)


def _get_stage_service(db: Session = Depends(get_db)) -> ExecutionStageService:
    return ExecutionStageService(db)


@router.post(
    "/investigations/{investigation_id}/executions",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_execution(
    investigation_id: uuid.UUID,
    body: CreateExecutionRequest,
    service: ExecutionService = Depends(_get_service),
) -> ExecutionResponse:
    """Create a new execution for an investigation."""
    logger.info(
        "execution_created",
        investigation_id=str(investigation_id),
        trigger=body.trigger,
    )
    return service.create_execution(investigation_id, body)


@router.get(
    "/investigations/{investigation_id}/executions",
    response_model=list[ExecutionResponse],
)
async def list_executions(
    investigation_id: uuid.UUID,
    service: ExecutionService = Depends(_get_service),
) -> list[ExecutionResponse]:
    """Return all executions for an investigation."""
    logger.info("executions_listed", investigation_id=str(investigation_id))
    return list(service.list_executions(investigation_id))


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionResponse,
)
async def get_execution(
    execution_id: uuid.UUID,
    service: ExecutionService = Depends(_get_service),
) -> ExecutionResponse:
    """Return a single execution by id."""
    execution = service.get_execution(execution_id)
    if execution is None:
        logger.warning("execution_not_found", id=str(execution_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("execution_retrieved", id=str(execution_id))
    return execution


@router.patch(
    "/executions/{execution_id}",
    response_model=ExecutionResponse,
)
async def update_execution(
    execution_id: uuid.UUID,
    body: UpdateExecutionRequest,
    service: ExecutionService = Depends(_get_service),
) -> ExecutionResponse:
    """Update an execution's status."""
    execution = service.update_execution(execution_id, body)
    if execution is None:
        logger.warning("execution_not_found", id=str(execution_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    logger.info("execution_updated", id=str(execution_id), status=execution.status.value)
    return execution


@router.get(
    "/executions/{execution_id}/stages",
    response_model=list[ExecutionStageResponse],
)
async def list_stages(
    execution_id: uuid.UUID,
    service: ExecutionStageService = Depends(_get_stage_service),
) -> list[ExecutionStageResponse]:
    """Return all stages for an execution, ordered by creation time."""
    return list(service.list_stages(execution_id))
