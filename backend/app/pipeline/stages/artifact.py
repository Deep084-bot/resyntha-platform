"""Artifact stage — creates a PAPER_COLLECTION artifact after papers
have been persisted.

Consumes ``context.artifacts["paper_ids"]`` (list of UUIDs).
Produces ``context.artifacts["artifact_response"]``
(``ArtifactResponse``).
"""

import uuid
from datetime import datetime

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage
from app.modules.artifact.domain.models import ArtifactType
from app.modules.artifact.schemas.request import CreateArtifactRequest
from app.modules.artifact.service.service import ArtifactService


class ArtifactStage(PipelineStage):
    """Create a PAPER_COLLECTION artifact with paper metadata."""

    consumes: list[str] = ["paper_ids"]
    produces: list[str] = ["artifact_response"]
    metadata: dict = {
        "description": "Create a PAPER_COLLECTION artifact",
    }

    def __init__(self, artifact_service: ArtifactService) -> None:
        self._artifact_service = artifact_service

    def name(self) -> str:
        return "artifact"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        paper_ids: list[uuid.UUID] | None = context.get_artifact("paper_ids")
        if not paper_ids:
            context.add_error("artifact", "No paper_ids found in context")
            return PipelineResult.FAILED

        investigation_id = context.investigation_id

        artifact = self._artifact_service.create_artifact(
            investigation_id=investigation_id,
            request=CreateArtifactRequest(
                artifact_type=ArtifactType.PAPER_COLLECTION,
                execution_id=context.execution_id,
                payload={
                    "paper_count": len(paper_ids),
                    "paper_ids": [str(pid) for pid in paper_ids],
                    "generated_at": datetime.utcnow().isoformat(),
                },
            ),
        )
        context.add_artifact("artifact_response", artifact)
        return PipelineResult.SUCCESS
