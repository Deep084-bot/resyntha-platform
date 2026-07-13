"""Persist stage — writes canonical papers to the database and links
them to the investigation.

Consumes ``context.artifacts["papers"]`` (list of canonical ``Paper``
DTOs).  Produces ``context.artifacts["paper_ids"]`` (list of UUIDs)
and records ``paper_count`` in metrics.
"""

import uuid
from collections.abc import Sequence

from app.modules.paper.service.service import PaperService
from app.modules.retrieval.domain.paper import Paper as PaperDTO
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage


class PersistStage(PipelineStage):
    """Create or reuse Paper records and attach them to the investigation."""

    consumes: list[str] = ["papers"]
    produces: list[str] = ["paper_ids"]
    metadata: dict = {
        "description": "Persist canonical papers and link to investigation",
    }

    def __init__(self, paper_service: PaperService) -> None:
        self._paper_service = paper_service

    def name(self) -> str:
        return "persist"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        papers: Sequence[PaperDTO] | None = context.get_artifact("papers")
        if not papers:
            context.add_error("persist", "No papers found in context")
            return PipelineResult.FAILED

        investigation_id = context.investigation_id
        paper_ids: list[uuid.UUID] = self._paper_service.persist_retrieved_papers(
            investigation_id,
            papers,
        )
        context.add_artifact("paper_ids", paper_ids)
        context.record_metric("paper_count", len(papers))
        return PipelineResult.SUCCESS
