"""Builds a ``KNOWLEDGE_PACKAGE`` artifact from extraction results.

The artifact's payload is a JSON structure containing per-paper
extracted knowledge that the frontend Knowledge tab can render.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact, ArtifactStatus, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.observability.logger import get_logger

logger = get_logger(__name__)


class ExtractionArtifactBuilder:
    """Creates a ``KNOWLEDGE_PACKAGE`` artifact summarising an extraction run."""

    def __init__(self, session: Session) -> None:
        self._artifact_repo = ArtifactRepository(session)

    def create_package(
        self,
        investigation_id: uuid.UUID,
        knowledge_records: Sequence[ExtractedKnowledge],
        execution_id: uuid.UUID | None = None,
    ) -> Artifact:
        """Persist a ``KNOWLEDGE_PACKAGE`` artifact.

        The payload is an object with a ``papers`` key containing a list
        of per-paper extraction results with paper_id, title, and the
        structured knowledge fields.
        """
        payload = {
            "papers": [
                {
                    "paper_id": str(r.paper_id),
                    "paper_title": r.paper_title,
                    "research_questions": r.research_questions,
                    "key_findings": r.key_findings,
                    "methodology": r.methodology,
                    "limitations": r.limitations,
                    "key_contributions": r.key_contributions,
                    "relevant_techniques": r.relevant_techniques,
                    "cited_works": r.cited_works,
                    "future_work": r.future_work,
                    "summary": r.summary,
                    "tokens_used": r.tokens_used,
                }
                for r in knowledge_records
            ],
        }

        artifact = Artifact(
            investigation_id=investigation_id,
            execution_id=execution_id,
            artifact_type=ArtifactType.KNOWLEDGE_PACKAGE,
            payload=payload,
            status=ArtifactStatus.READY,
        )

        created = self._artifact_repo.create(artifact)
        logger.info(
            "knowledge_package_artifact_created",
            artifact_id=str(created.id),
            investigation_id=str(investigation_id),
            paper_count=len(knowledge_records),
        )
        return created
