"""AnalyzeStage — runs cross-paper analysis on extracted knowledge.

Consumes ``extracted_knowledge_ids`` produced by ExtractStage and
produces a ``RESEARCH_LANDSCAPE`` artifact with aggregated statistics,
frequencies, and clusters.

No LLM calls — purely deterministic aggregation.
"""

from app.modules.analysis.service.service import AnalysisService
from app.observability.logger import get_logger
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage

logger = get_logger(__name__)


class AnalyzeStage(PipelineStage):
    """Run deterministic cross-paper analysis on extracted knowledge.

    Parameters
    ----------
    analysis_service:
        Fully initialised ``AnalysisService``.
    """

    consumes: list[str] = ["extracted_knowledge_ids"]
    produces: list[str] = ["research_landscape"]
    metadata: dict = {
        "description": "Run deterministic cross-paper analysis on extracted knowledge",
    }

    def __init__(self, analysis_service: AnalysisService) -> None:
        self._analysis_service = analysis_service

    def name(self) -> str:
        return "analyze"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        investigation_id = context.investigation_id
        execution_id = context.execution_id

        logger.info(
            "analyze_stage_started",
            investigation_id=str(investigation_id),
        )

        try:
            landscape = await self._analysis_service.analyze(
                investigation_id=investigation_id,
                execution_id=execution_id,
            )

            context.record_metric("papers_analyzed", landscape.paper_count)
            context.record_metric(
                "clusters_generated",
                sum(len(v) for v in landscape.clusters.values()),
            )

            logger.info(
                "analyze_stage_completed",
                investigation_id=str(investigation_id),
                paper_count=landscape.paper_count,
            )

            return PipelineResult.SUCCESS

        except Exception as exc:
            logger.exception(
                "analyze_stage_failed",
                investigation_id=str(investigation_id),
            )
            context.add_error("analyze", str(exc), exc)
            return PipelineResult.FAILED
