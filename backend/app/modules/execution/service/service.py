"""Execution service."""

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.execution.domain.models import Execution, ExecutionStatus
from app.modules.execution.repository.repository import ExecutionRepository
from app.modules.execution.schemas.request import (
    CreateExecutionRequest,
    UpdateExecutionRequest,
)
from app.modules.execution.schemas.response import ExecutionResponse
from app.observability.logger import get_logger

logger = get_logger(__name__)


class ExecutionService:
    """Encapsulates execution business logic."""

    def __init__(self, session: Session) -> None:
        self._repository = ExecutionRepository(session)
        self._session = session

    def create_execution(
        self,
        investigation_id: uuid.UUID,
        request: CreateExecutionRequest,
    ) -> ExecutionResponse:
        """Create a new execution in PENDING status."""
        execution = Execution(
            investigation_id=investigation_id,
            status=ExecutionStatus.PENDING,
            trigger=request.trigger,
            created_by=request.created_by,
        )
        saved = self._repository.create(execution)
        self._session.commit()
        return ExecutionResponse.model_validate(saved)

    def get_execution(
        self, execution_id: uuid.UUID,
    ) -> ExecutionResponse | None:
        """Return an execution by id, or ``None``."""
        execution = self._repository.get_by_id(execution_id)
        if execution is None:
            return None
        return ExecutionResponse.model_validate(execution)

    def list_executions(
        self, investigation_id: uuid.UUID,
    ) -> Sequence[ExecutionResponse]:
        """Return all executions for an investigation."""
        executions = self._repository.list_by_investigation(investigation_id)
        return [ExecutionResponse.model_validate(e) for e in executions]

    def update_execution(
        self,
        execution_id: uuid.UUID,
        request: UpdateExecutionRequest,
    ) -> ExecutionResponse | None:
        """Update an execution's status.

        Automatically sets ``started_at`` when transitioning to RUNNING
        and ``completed_at`` when transitioning to a terminal state
        (COMPLETED, FAILED, CANCELLED).

        Returns ``None`` when the execution does not exist.
        """
        execution = self._repository.get_by_id(execution_id)
        if execution is None:
            return None

        if request.status is not None:
            execution.status = request.status
            if request.status == ExecutionStatus.RUNNING:
                execution.started_at = datetime.now(timezone.utc)
            if request.status in (
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            ):
                execution.completed_at = datetime.now(timezone.utc)

        updated = self._repository.update(execution)
        self._session.commit()
        return ExecutionResponse.model_validate(updated)
