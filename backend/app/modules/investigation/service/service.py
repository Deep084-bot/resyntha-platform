"""Investigation service.

Implements the business rules around investigation lifecycle.
The service depends on a repository and a session for transaction
control.
"""

import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.execution.domain.models import Execution, ExecutionStatus
from app.modules.investigation.domain.models import (
    Investigation,
    InvestigationStatus,
)
from app.modules.investigation.repository.repository import (
    InvestigationRepository,
)
from app.modules.investigation.schemas.request import (
    CreateInvestigationRequest,
)
from app.modules.investigation.schemas.response import (
    InvestigationResponse,
)
from app.modules.investigation.timeline.models import (
    TimelineStage,
    TimelineStatus,
)
from app.modules.investigation.timeline.schemas import (
    TimelineEventResponse,
)
from app.modules.investigation.timeline.service import (
    TimelineService,
)


class InvestigationService:
    """Encapsulates investigation business logic."""

    def __init__(self, session: Session) -> None:
        self._repository = InvestigationRepository(session)
        self._timeline = TimelineService(session)
        self._session = session

    def create_investigation(self, request: CreateInvestigationRequest) -> InvestigationResponse:
        """Create a new investigation and return its response representation."""
        from app.metrics import get_metrics_service

        get_metrics_service().investigation_created_total.inc()
        investigation = Investigation(
            title=request.title,
            topic=request.topic,
            paper_limit=request.paper_limit,
            status=InvestigationStatus.CREATED,
        )
        saved = self._repository.create(investigation)

        self._timeline.record_event(
            investigation_id=saved.id,
            stage=TimelineStage.CREATED,
            status=TimelineStatus.SUCCESS,
            message="Investigation created",
        )

        self._session.commit()
        return InvestigationResponse.model_validate(saved)

    def get_investigation(self, investigation_id: uuid.UUID) -> InvestigationResponse | None:
        """Return an investigation by id, or ``None`` if not found."""
        investigation = self._repository.get_by_id(investigation_id)
        if investigation is None:
            return None
        return InvestigationResponse.model_validate(investigation)

    def list_investigations(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[InvestigationResponse]:
        """Return a paginated list of all investigations."""
        investigations = self._repository.list(skip=skip, limit=limit)
        return [InvestigationResponse.model_validate(i) for i in investigations]

    def delete_investigation(self, investigation_id: uuid.UUID) -> bool:
        """Delete an investigation.  Returns ``True`` if it existed."""
        investigation = self._repository.get_by_id(investigation_id)
        if investigation is None:
            return False

        active = self._session.scalar(
            select(Execution)
            .where(
                Execution.investigation_id == investigation_id,
                Execution.status.in_([ExecutionStatus.PENDING, ExecutionStatus.RUNNING]),
            )
            .limit(1)
        )
        if active is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete investigation with a running execution",
            )

        self._repository.delete(investigation)
        self._session.commit()
        return True

    def get_timeline(self, investigation_id: uuid.UUID) -> Sequence[TimelineEventResponse]:
        """Return the timeline for an investigation."""
        return self._timeline.get_timeline(investigation_id)
