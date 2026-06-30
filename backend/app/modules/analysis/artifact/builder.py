"""Creates ``RESEARCH_LANDSCAPE`` artifacts from analysis results.

The artifact's payload contains the full ``ResearchLandscape`` dict,
which the frontend Analysis tab renders.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.analysis.domain.landscape import ResearchLandscape
from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)


class AnalysisArtifactBuilder:
    """Creates a ``RESEARCH_LANDSCAPE`` artifact for an investigation."""

    def __init__(self, session: Session) -> None:
        self._artifact_repo = ArtifactRepository(session)

    def create_landscape_artifact(
        self,
        investigation_id: uuid.UUID,
        landscape: ResearchLandscape,
        execution_id: uuid.UUID | None = None,
    ) -> Artifact:
        """Persist a ``RESEARCH_LANDSCAPE`` artifact."""
        payload = landscape.model_dump()
        payload["generated_at"] = datetime.now(UTC).isoformat()

        artifact = Artifact(
            investigation_id=investigation_id,
            execution_id=execution_id,
            artifact_type=ArtifactType.RESEARCH_LANDSCAPE,
            payload=payload,
        )

        created = self._artifact_repo.create(artifact)
        logger.info(
            "research_landscape_artifact_created",
            artifact_id=str(created.id),
            investigation_id=str(investigation_id),
            paper_count=landscape.paper_count,
        )
        return created
