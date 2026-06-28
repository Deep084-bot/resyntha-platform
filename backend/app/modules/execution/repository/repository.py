"""Execution repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.execution.domain.models import Execution


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
