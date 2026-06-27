"""Retrieval workflow — coordinates the full paper-retrieval process.

Flow
----
1. Load the investigation (fail fast if missing).
2. Record a RUNNING timeline event.
3. Execute RetrievalService.retrieve().
4. Persist papers via PaperService.
5. Create a PAPER_COLLECTION artifact via ArtifactService.
6. Record a SUCCESS timeline event.
7. Return ``RetrievalWorkflowResponse``.

On any failure a FAILURE timeline event is recorded before the
exception propagates.
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import ArtifactType
from app.modules.artifact.schemas.request import CreateArtifactRequest
from app.modules.artifact.service.service import ArtifactService
from app.modules.investigation.service.service import InvestigationService
from app.modules.investigation.timeline.models import TimelineStage, TimelineStatus
from app.modules.investigation.timeline.service import TimelineService
from app.modules.paper.service.service import PaperService
from app.modules.retrieval.schemas.response import RetrieveResponse
from app.modules.retrieval.service.service import RetrievalService
from app.observability.logger import get_logger

logger = get_logger(__name__)


class RetrievalWorkflow:
    """Orchestrate the retrieval pipeline end-to-end."""

    def __init__(self, db: Session) -> None:
        self._session = db
        self._retrieval_service = RetrievalService()
        self._paper_service = PaperService(db)
        self._artifact_service = ArtifactService(db)
        self._timeline_service = TimelineService(db)
        self._investigation_service = InvestigationService(db)

    async def run(
        self,
        investigation_id: uuid.UUID,
        query: str,
        paper_limit: int = 10,
    ) -> RetrieveResponse:
        """Execute the retrieval workflow and return the result.

        Raises ``ValueError`` when the investigation does not exist.
        """
        investigation = self._investigation_service.get_investigation(
            investigation_id,
        )
        if investigation is None:
            raise ValueError(f"Investigation {investigation_id} not found")

        self._timeline_service.record_event(
            investigation_id=investigation_id,
            stage=TimelineStage.RETRIEVING,
            status=TimelineStatus.RUNNING,
            message="Paper retrieval started",
        )

        try:
            papers = await self._retrieval_service.retrieve(
                query, paper_limit,
            )

            paper_ids = self._paper_service.persist_retrieved_papers(
                investigation_id, papers,
            )

            logger.info(
                "workflow_papers_persisted",
                investigation_id=str(investigation_id),
                count=len(papers),
            )

            artifact_response = self._artifact_service.create_artifact(
                investigation_id=investigation_id,
                request=CreateArtifactRequest(
                    artifact_type=ArtifactType.PAPER_COLLECTION,
                    payload={
                        "paper_count": len(papers),
                        "paper_ids": [str(pid) for pid in paper_ids],
                        "generated_at": datetime.utcnow().isoformat(),
                    },
                ),
            )

            self._timeline_service.record_event(
                investigation_id=investigation_id,
                stage=TimelineStage.RETRIEVING,
                status=TimelineStatus.SUCCESS,
                message=f"Retrieved {len(papers)} papers",
            )
            self._session.commit()

            logger.info(
                "workflow_completed",
                investigation_id=str(investigation_id),
                paper_count=len(papers),
                artifact_id=str(artifact_response.id),
            )

            return RetrieveResponse(
                investigation_id=investigation_id,
                artifact_id=artifact_response.id,
                paper_count=len(papers),
            )

        except Exception:
            self._timeline_service.record_event(
                investigation_id=investigation_id,
                stage=TimelineStage.RETRIEVING,
                status=TimelineStatus.FAILURE,
                message="Retrieval failed",
            )
            self._safe_commit()
            raise

    def _safe_commit(self) -> None:
        """Attempt to commit; roll back on failure to keep the session usable."""
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
