"""Artifact stage — creates artifacts after papers have been persisted
and validated.

Produces a ``PAPER_COLLECTION`` artifact from ``paper_ids`` and,
when validation data is present, a ``VALIDATED_COLLECTION`` artifact
with the validation summary and per-paper results.
"""

import uuid
from datetime import datetime
from typing import Any

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage
from app.modules.artifact.domain.models import ArtifactType
from app.modules.artifact.schemas.request import CreateArtifactRequest
from app.modules.artifact.service.service import ArtifactService


class ArtifactStage(PipelineStage):
    """Create PAPER_COLLECTION (+ optionally VALIDATED_COLLECTION) artifacts."""

    consumes: list[str] = ["paper_ids"]
    produces: list[str] = ["artifact_response"]
    metadata: dict = {
        "description": "Create paper and validation artifacts",
    }

    def __init__(self, artifact_service: ArtifactService) -> None:
        self._artifact_service = artifact_service

    def name(self) -> str:
        return "artifact"

    def _make_payload(self, **kwargs: Any) -> dict[str, Any]:
        return {**kwargs, "generated_at": datetime.utcnow().isoformat()}

    async def execute(self, context: PipelineContext) -> PipelineResult:
        paper_ids: list[uuid.UUID] | None = context.get_artifact("paper_ids")
        if not paper_ids:
            context.add_error("artifact", "No paper_ids found in context")
            return PipelineResult.FAILED

        investigation_id = context.investigation_id

        # ── PAPER_COLLECTION (unchanged) ─────────────────────────
        paper_artifact = self._artifact_service.create_artifact(
            investigation_id=investigation_id,
            request=CreateArtifactRequest(
                artifact_type=ArtifactType.PAPER_COLLECTION,
                execution_id=context.execution_id,
                payload=self._make_payload(
                    paper_count=len(paper_ids),
                    paper_ids=[str(pid) for pid in paper_ids],
                ),
            ),
        )
        context.add_artifact("artifact_response", paper_artifact)

        # ── VALIDATED_COLLECTION (when validation ran) ───────────
        validated_papers: list[dict[str, Any]] | None = context.get_artifact("validated_papers")
        if validated_papers is not None:
            total = len(validated_papers)
            valid = sum(1 for v in validated_papers if v.get("validation_status") == "valid")
            warning = sum(1 for v in validated_papers if v.get("validation_status") == "warning")
            invalid = sum(1 for v in validated_papers if v.get("validation_status") == "invalid")
            duplicates = sum(
                1 for v in validated_papers
                if any("duplicate" in (msg or "") for msg in v.get("validation_messages", []))
            )
            scores = [v.get("validation_score", 0) for v in validated_papers]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

            validation_artifact = self._artifact_service.create_artifact(
                investigation_id=investigation_id,
                request=CreateArtifactRequest(
                    artifact_type=ArtifactType.VALIDATED_COLLECTION,
                    execution_id=context.execution_id,
                    payload=self._make_payload(
                        validated_papers=validated_papers,
                        summary={
                            "total_papers": total,
                            "valid": valid,
                            "warning": warning,
                            "invalid": invalid,
                            "duplicates": duplicates,
                            "average_score": avg_score,
                        },
                    ),
                ),
            )
            context.add_artifact("validation_artifact_response", validation_artifact)

        return PipelineResult.SUCCESS
