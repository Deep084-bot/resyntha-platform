"""Investigation repository.

Provides CRUD operations on the ``Investigation`` model.  No business
logic lives here — the repository simply translates between the ORM
and the caller.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.investigation.domain.models import Investigation


class InvestigationRepository:
    """Persistence gateway for ``Investigation`` aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, investigation: Investigation) -> Investigation:
        """Persist a new investigation and return it with its generated id."""
        self._session.add(investigation)
        self._session.flush()
        self._session.refresh(investigation)
        return investigation

    def get_by_id(self, investigation_id: uuid.UUID) -> Investigation | None:
        """Return an investigation by primary key, or ``None``."""
        return self._session.get(Investigation, investigation_id)

    def list(self, skip: int = 0, limit: int = 100) -> Sequence[Investigation]:
        """Return a paginated list of investigations ordered by creation date."""
        stmt = (
            select(Investigation)
            .order_by(Investigation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self._session.scalars(stmt).all()

    def delete(self, investigation: Investigation) -> None:
        """Remove an investigation from the session."""
        self._session.delete(investigation)
        self._session.flush()
