"""Timeline repository.

Provides persistence operations for ``InvestigationTimeline``
entries.  No business logic lives here.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.investigation.timeline.models import (
    InvestigationTimeline,
)


class TimelineRepository:
    """Persistence gateway for timeline events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append_event(
        self, event: InvestigationTimeline
    ) -> InvestigationTimeline:
        """Persist a new timeline event and return it with its generated id."""
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event

    def list_events(
        self, investigation_id: uuid.UUID
    ) -> Sequence[InvestigationTimeline]:
        """Return all timeline events for an investigation, oldest first."""
        stmt = (
            select(InvestigationTimeline)
            .where(
                InvestigationTimeline.investigation_id == investigation_id
            )
            .order_by(InvestigationTimeline.created_at.asc())
        )
        return self._session.scalars(stmt).all()
