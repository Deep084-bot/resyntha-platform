"""GapDetectionStage — runs rule-based research gap detection.

Consumes extracted knowledge (already in the database) and produces
a ``RESEARCH_GAP_REPORT`` artifact with identified gaps, opportunities,
and recommendations.

No LLM calls — purely deterministic rule evaluation.
"""

from app.modules.gap_detection.service.service import GapDetectionService
from app.observability.logger import get_logger
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage

logger = get_logger(__name__)


class GapDetectionStage(PipelineStage):
    """Run deterministic rule-based research gap detection.

    Parameters
    ----------
    gap_detection_service:
        Fully initialised ``GapDetectionService``.
    """

    consumes: list[str] = []
    produces: list[str] = ["research_gap_report"]
    metadata: dict = {
        "description": "Run deterministic rule-based research gap detection",
    }

    def __init__(self, gap_detection_service: GapDetectionService) -> None:
        self._gap_service = gap_detection_service

    def name(self) -> str:
        return "gap_detection"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        investigation_id = context.investigation_id
        execution_id = context.execution_id

        logger.info(
            "gap_detection_stage_started",
            investigation_id=str(investigation_id),
        )

        try:
            report = await self._gap_service.detect_gaps(
                investigation_id=investigation_id,
                execution_id=execution_id,
            )

            context.record_metric("gaps_found", report.summary.total_gaps)
            context.record_metric(
                "high_confidence_gaps",
                report.summary.high_confidence_gaps,
            )

            logger.info(
                "gap_detection_stage_completed",
                investigation_id=str(investigation_id),
                total_gaps=report.summary.total_gaps,
                high_confidence=report.summary.high_confidence_gaps,
            )

            return PipelineResult.SUCCESS

        except Exception as exc:
            logger.exception(
                "gap_detection_stage_failed",
                investigation_id=str(investigation_id),
            )
            context.add_error("gap_detection", str(exc), exc)
            return PipelineResult.FAILED
