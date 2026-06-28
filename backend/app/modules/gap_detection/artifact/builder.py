"""Creates ``RESEARCH_GAP_REPORT`` artifacts from gap detection results.

The artifact's payload contains the full ``ResearchGapReport`` dict,
which the frontend Research Gaps tab renders.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.gap_detection.domain.gap import ResearchGapReport
from app.observability.logger import get_logger

logger = get_logger(__name__)


class GapArtifactBuilder:
    """Creates a ``RESEARCH_GAP_REPORT`` artifact for an investigation."""

    def __init__(self, session: AsyncSession) -> None:
        self._artifact_repo = ArtifactRepository(session)

    async def create_gap_report_artifact(
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
            name=f"Research Gap Report — {report.summary.total_gaps} gaps",
            description=(
                f"Gap analysis of {report.summary.total_gaps} gaps "
                f"({report.summary.high_confidence_gaps} high confidence)"
            ),
            payload=payload,
        )

        created = await self._artifact_repo.create(artifact)
        logger.info(
            "gap_report_artifact_created",
            artifact_id=str(created.id),
            investigation_id=str(investigation_id),
            gap_count=report.summary.total_gaps,
        )
        return created
