"""Retrieve stage — searches external providers for papers matching a query.

Reads ``query`` and ``paper_limit`` from ``context.metadata``.
Stores the canonical ``Paper`` list in ``context.artifacts["papers"]``.
"""

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage
from app.modules.retrieval.service.service import RetrievalService


class RetrieveStage(PipelineStage):
    """Search Semantic Scholar and arXiv, normalise, deduplicate, rank."""

    consumes: list[str] = []
    produces: list[str] = ["papers"]
    metadata: dict = {
        "description": "Search external providers and return canonical papers",
    }

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
    ) -> None:
        self._service = retrieval_service or RetrievalService()

    def name(self) -> str:
        return "retrieve"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        query: str | None = context.metadata.get("query")
        paper_limit: int = context.metadata.get("paper_limit", 10)

        if not query:
            context.add_error("retrieve", "No query found in context metadata")
            return PipelineResult.FAILED

        papers = await self._service.retrieve(query, paper_limit)
        context.add_artifact("papers", papers)
        return PipelineResult.SUCCESS
