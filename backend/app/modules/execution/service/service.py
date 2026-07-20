"""Execution service."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.execution.domain.models import (
    Execution,
    ExecutionStage,
    ExecutionStageStatus,
    ExecutionStatus,
)
from app.modules.execution.repository.repository import (
    ExecutionRepository,
    ExecutionStageRepository,
)
from app.modules.execution.schemas.request import (
    CreateExecutionRequest,
    UpdateExecutionRequest,
)
from app.modules.execution.schemas.response import (
    ExecutionResponse,
    ExecutionStageResponse,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)


class ExecutionService:
    """Encapsulates execution business logic."""

    def __init__(self, session: Session) -> None:
        self._repository = ExecutionRepository(session)
        self._session = session

    def has_active_execution(self, investigation_id: uuid.UUID) -> bool:
        """Return ``True`` if the investigation has a PENDING or RUNNING execution."""
        stmt = (
            select(Execution)
            .where(
                Execution.investigation_id == investigation_id,
                Execution.status.in_([ExecutionStatus.PENDING, ExecutionStatus.RUNNING]),
            )
            .limit(1)
            .with_for_update()
        )
        return self._session.scalar(stmt) is not None

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
        self,
        execution_id: uuid.UUID,
    ) -> ExecutionResponse | None:
        """Return an execution by id, or ``None``."""
        execution = self._repository.get_by_id(execution_id)
        if execution is None:
            return None
        return ExecutionResponse.model_validate(execution)

    def list_executions(
        self,
        investigation_id: uuid.UUID,
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
                execution.started_at = datetime.now(UTC)
            if request.status in (
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            ):
                execution.completed_at = datetime.now(UTC)

        updated = self._repository.update(execution)
        self._session.commit()
        return ExecutionResponse.model_validate(updated)

    def update_metadata(
        self,
        execution_id: uuid.UUID,
        metadata: dict,
    ) -> bool:
        """Merge metadata into an execution's JSONB column.

        Returns ``True`` if the execution was found and updated.
        """
        execution = self._repository.get_by_id(execution_id)
        if execution is None:
            return False
        current = execution._metadata or {}
        current.update(metadata)
        execution._metadata = current
        self._repository.update(execution)
        self._session.commit()
        return True


class ExecutionStageService:
    """Encapsulates execution-stage business logic.

    Implements ``StageRecorder`` protocol so the pipeline runner can
    record stage lifecycle events without depending on SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        self._repository = ExecutionStageRepository(session)
        self._session = session

    async def record_started(
        self,
        execution_id: uuid.UUID,
        stage_name: str,
        attempt: int,
    ) -> None:
        """Record that a stage attempt has begun."""
        stage = ExecutionStage(
            execution_id=execution_id,
            stage_name=stage_name,
            status=ExecutionStageStatus.RUNNING,
            attempt=attempt,
            started_at=datetime.now(UTC),
        )
        self._repository.create(stage)
        self._session.commit()
        logger.info(
            "stage_started",
            execution_id=str(execution_id),
            stage=stage_name,
            attempt=attempt,
        )

    async def record_completed(
        self,
        execution_id: uuid.UUID,
        stage_name: str,
        metadata: dict | None = None,
    ) -> None:
        """Record that a stage attempt completed successfully.

        When *metadata* is provided the stage is recorded as
        ``PARTIAL_SUCCESS`` and the metadata is persisted in the
        stage's JSONB column.
        """
        stage = self._repository.get_active_stage(execution_id, stage_name)
        if stage is None:
            logger.warning(
                "stage_not_found_for_completion",
                execution_id=str(execution_id),
                stage=stage_name,
            )
            return
        now = datetime.now(UTC)
        if metadata is not None:
            stage.status = ExecutionStageStatus.PARTIAL_SUCCESS
            stage._metadata = metadata
        else:
            stage.status = ExecutionStageStatus.COMPLETED
        stage.completed_at = now
        if stage.started_at:
            stage.duration_ms = int((now - stage.started_at).total_seconds() * 1000)
        self._repository.update(stage)
        self._session.commit()

    async def record_failed(
        self,
        execution_id: uuid.UUID,
        stage_name: str,
        error_message: str,
    ) -> None:
        """Record that a stage attempt failed."""
        stage = self._repository.get_active_stage(execution_id, stage_name)
        if stage is None:
            logger.warning(
                "stage_not_found_for_failure",
                execution_id=str(execution_id),
                stage=stage_name,
            )
            return
        now = datetime.now(UTC)
        stage.status = ExecutionStageStatus.FAILED
        stage.completed_at = now
        if stage.started_at:
            stage.duration_ms = int((now - stage.started_at).total_seconds() * 1000)
        stage.error_message = error_message
        self._repository.update(stage)
        self._session.commit()

    def list_stages(
        self,
        execution_id: uuid.UUID,
    ) -> Sequence[ExecutionStageResponse]:
        """Return all stages for an execution, oldest first."""
        stages = self._repository.list_by_execution(execution_id)
        return [ExecutionStageResponse.model_validate(s) for s in stages]
