"""Timeline stage — records pipeline completion in the investigation
timeline.

This stage runs last and only executes when all prior stages
succeeded.  It reads ``context.execution_state`` to determine the
outcome and records a SUCCESS event.  The RUNNING and FAILURE events
are owned by the API route (which invokes the pipeline).
"""

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage
from app.modules.investigation.timeline.models import TimelineStage as TimelineStageEnum
from app.modules.investigation.timeline.models import TimelineStatus
from app.modules.investigation.timeline.service import TimelineService


class TimelineStage(PipelineStage):
    """Record a SUCCESS timeline event after the pipeline completes."""

    consumes: list[str] = []
    produces: list[str] = ["timeline_recorded"]
    metadata: dict = {
        "description": "Record pipeline completion in the investigation timeline",
    }

    # Maps pipeline-level stage names to TimelineStage enum values.
    _STAGE_MAP: dict[str, TimelineStageEnum] = {
        "retrieving": TimelineStageEnum.RETRIEVING,
        "extracting": TimelineStageEnum.EXTRACTING,
        "analyzing": TimelineStageEnum.ANALYZING,
        "generating": TimelineStageEnum.GENERATING,
    }

    def __init__(self, timeline_service: TimelineService) -> None:
        self._timeline_service = timeline_service

    def name(self) -> str:
        return "timeline"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        investigation_id = context.investigation_id
        stage_name: str = context.metadata.get("timeline_stage", "retrieving")
        timeline_stage = self._STAGE_MAP.get(stage_name, TimelineStageEnum.RETRIEVING)

        paper_count = context.metrics.get("paper_count", 0)
        message = f"Retrieved {paper_count} papers"

        self._timeline_service.record_event(
            investigation_id=investigation_id,
            stage=timeline_stage,
            status=TimelineStatus.SUCCESS,
            message=message,
        )

        context.add_artifact("timeline_recorded", True)
        return PipelineResult.SUCCESS
