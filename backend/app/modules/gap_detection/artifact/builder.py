"""Creates ``RESEARCH_GAP_REPORT`` artifacts from gap detection results.

The artifact's payload contains the full ``ResearchGapReport`` dict,
which the frontend Research Gaps tab renders.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.gap_detection.domain.gap import ResearchGapReport
from app.observability.logger import get_logger

logger = get_logger(__name__)


class GapArtifactBuilder:
    """Creates a ``RESEARCH_GAP_REPORT`` artifact for an investigation."""

    def __init__(self, session: Session) -> None:
        self._artifact_repo = ArtifactRepository(session)

    def create_gap_report_artifact(
        self,
        investigation_id: uuid.UUID,
        report: ResearchGapReport,
        execution_id: uuid.UUID | None = None,
    ) -> Artifact:
        """Persist a ``RESEARCH_GAP_REPORT`` artifact."""
        payload = report.model_dump()
        payload["generated_at"] = datetime.now(UTC).isoformat()

        artifact = Artifact(
            investigation_id=investigation_id,
            execution_id=execution_id,
            artifact_type=ArtifactType.RESEARCH_GAP_REPORT,
            payload=payload,
        )

        created = self._artifact_repo.create(artifact)
        logger.info(
            "gap_report_artifact_created",
            artifact_id=str(created.id),
            investigation_id=str(investigation_id),
            gap_count=report.summary.total_gaps,
        )
        return created
