"""Execution repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.execution.domain.models import Execution, ExecutionStage


class ExecutionRepository:
    """Persistence gateway for ``Execution`` aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, execution: Execution) -> Execution:
        """Persist a new execution and return it with its generated id."""
        self._session.add(execution)
        self._session.flush()
        self._session.refresh(execution)
        return execution

    def get_by_id(self, execution_id: uuid.UUID) -> Execution | None:
        """Return an execution by primary key, or ``None``."""
        return self._session.get(Execution, execution_id)

    def list_by_investigation(
        self, investigation_id: uuid.UUID,
    ) -> Sequence[Execution]:
        """Return all executions for an investigation, newest first."""
        stmt = (
            select(Execution)
            .where(Execution.investigation_id == investigation_id)
            .order_by(Execution.created_at.desc())
        )
        return self._session.scalars(stmt).all()

    def update(self, execution: Execution) -> Execution:
        """Flush changes made to an already-attached execution."""
        self._session.flush()
        self._session.refresh(execution)
        return execution


class ExecutionStageRepository:
    """Persistence gateway for ``ExecutionStage`` aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, stage: ExecutionStage) -> ExecutionStage:
        """Persist a new stage record and return it."""
        self._session.add(stage)
        self._session.flush()
        self._session.refresh(stage)
        return stage

    def get_by_id(self, stage_id: uuid.UUID) -> ExecutionStage | None:
        """Return a stage by primary key, or ``None``."""
        return self._session.get(ExecutionStage, stage_id)

    def get_active_stage(
        self, execution_id: uuid.UUID, stage_name: str,
    ) -> ExecutionStage | None:
        """Return the most recent non-terminal stage for the given execution
        and stage name, or ``None``."""
        stmt = (
            select(ExecutionStage)
            .where(
                ExecutionStage.execution_id == execution_id,
                ExecutionStage.stage_name == stage_name,
                ExecutionStage.status.in_(["pending", "running"]),
            )
            .order_by(ExecutionStage.created_at.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def list_by_execution(
        self, execution_id: uuid.UUID,
    ) -> Sequence[ExecutionStage]:
        """Return all stages for an execution, ordered by creation time."""
        stmt = (
            select(ExecutionStage)
            .where(ExecutionStage.execution_id == execution_id)
            .order_by(ExecutionStage.created_at.asc())
        )
        return self._session.scalars(stmt).all()

    def update(self, stage: ExecutionStage) -> ExecutionStage:
        """Flush changes to an already-attached stage."""
        self._session.flush()
        self._session.refresh(stage)
        return stage
