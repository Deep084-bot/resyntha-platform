"""ExtractStage — runs LLM-based knowledge extraction on persisted papers.

Consumes ``paper_ids`` produced by the PersistStage and produces
``extracted_knowledge_ids`` plus a ``KNOWLEDGE_PACKAGE`` artifact.
"""

from app.modules.extraction.service.service import ExtractionService
from app.observability.logger import get_logger
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage

logger = get_logger(__name__)


class ExtractStage(PipelineStage):
    """Run LLM-based knowledge extraction on persisted papers.

    Parameters
    ----------
    extraction_service:
        Fully initialised ``ExtractionService`` with LLM provider.
    """

    consumes: list[str] = ["paper_ids"]
    produces: list[str] = ["extracted_knowledge_ids"]
    metadata: dict = {
        "description": "Run LLM-based knowledge extraction on persisted papers",
    }

    def __init__(self, extraction_service: ExtractionService) -> None:
        self._extraction_service = extraction_service

    def name(self) -> str:
        return "extract"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        investigation_id = context.investigation_id
        execution_id = context.execution_id

        logger.info(
            "extract_stage_started",
            investigation_id=str(investigation_id),
        )

        try:
            results = await self._extraction_service.extract_for_investigation(
                investigation_id=investigation_id,
                execution_id=execution_id,
            )

            knowledge_ids = [str(k.id) for k in results]
            context.set_metadata("extracted_knowledge_ids", knowledge_ids)
            context.record_metric("extraction_count", len(results))

            logger.info(
                "extract_stage_completed",
                investigation_id=str(investigation_id),
                extraction_count=len(results),
            )

            return PipelineResult.SUCCESS

        except Exception as exc:
            logger.exception(
                "extract_stage_failed",
                investigation_id=str(investigation_id),
            )
            context.add_error("extract", str(exc), exc)
            return PipelineResult.FAILED
