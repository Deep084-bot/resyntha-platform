"""Timeline service.

Provides high-level operations for recording and querying timeline
events.  The service does not commit — callers are responsible for
transaction boundaries.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.investigation.timeline.models import (
    InvestigationTimeline,
    TimelineStage,
    TimelineStatus,
)
from app.modules.investigation.timeline.repository import (
    TimelineRepository,
)
from app.modules.investigation.timeline.schemas import (
    TimelineEventResponse,
)


class TimelineService:
    """Encapsulates timeline business rules."""

    def __init__(self, session: Session) -> None:
        self._repository = TimelineRepository(session)

    def record_event(
        self,
        investigation_id: uuid.UUID,
        stage: TimelineStage,
        status: TimelineStatus,
        message: str,
    ) -> None:
        """Append a new event to the investigation's timeline.

        The caller owns the transaction — this method only flushes.
        """
        event = InvestigationTimeline(
            investigation_id=investigation_id,
            stage=stage,
            status=status,
            message=message,
        )
        self._repository.append_event(event)

    def get_timeline(
        self, investigation_id: uuid.UUID
    ) -> Sequence[TimelineEventResponse]:
        """Return all timeline events for an investigation."""
        events = self._repository.list_events(investigation_id)
        return [TimelineEventResponse.model_validate(e) for e in events]
