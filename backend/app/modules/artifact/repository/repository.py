"""Artifact repository.

Provides persistence operations on the ``Artifact`` model.  The
repository is stateless with respect to business rules — it simply
maps between the ORM and the caller.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact


class ArtifactRepository:
    """Persistence gateway for ``Artifact`` aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, artifact: Artifact) -> Artifact:
        """Persist a new artifact and return it with its generated id."""
        self._session.add(artifact)
        self._session.flush()
        self._session.refresh(artifact)
        return artifact

    def get_by_id(self, artifact_id: uuid.UUID) -> Artifact | None:
        """Return an artifact by primary key, or ``None``."""
        return self._session.get(Artifact, artifact_id)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[Artifact]:
        """Return all artifacts for an investigation, newest first."""
        stmt = (
            select(Artifact)
            .where(Artifact.investigation_id == investigation_id)
            .order_by(Artifact.created_at.desc())
        )
        return self._session.scalars(stmt).all()

    def update(self, artifact: Artifact) -> Artifact:
        """Flush changes made to an already-attached artifact."""
        self._session.flush()
        self._session.refresh(artifact)
        return artifact
