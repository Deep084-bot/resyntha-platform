"""Wrapper plugins that delegate to existing pipeline stages.

Each plugin class internally instantiates the corresponding stage
and forwards ``execute()`` calls to it.  Business logic lives in
the stages — never duplicated here.
"""

from app.pipeline.stages import (
    AnalyzeStage,
    ArtifactStage,
    ExtractStage,
    GapDetectionStage,
    PersistStage,
    RetrieveStage,
    TimelineStage,
    ValidateStage,
)
from app.plugins.base import PipelinePlugin


class RetrievePlugin(PipelinePlugin):
    """Search external providers and return canonical papers."""

    _name = "retrieve"
    consumes: list[str] = []
    produces: list[str] = ["papers"]
    metadata: dict = {
        "description": "Search external providers and return canonical papers",
    }

    def __init__(self, **kwargs) -> None:
        retrieval_service = kwargs.get("retrieval_service")
        self._inner = RetrieveStage(retrieval_service=retrieval_service)

    async def execute(self, context):
        return await self._inner.execute(context)


class PersistPlugin(PipelinePlugin):
    """Create or reuse Paper records and attach them to the investigation."""

    _name = "persist"
    consumes: list[str] = ["papers"]
    produces: list[str] = ["paper_ids"]
    metadata: dict = {
        "description": "Persist canonical papers and link to investigation",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = PersistStage(paper_service=kwargs["paper_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class ArtifactPlugin(PipelinePlugin):
    """Create a PAPER_COLLECTION artifact after papers have been persisted."""

    _name = "artifact"
    consumes: list[str] = ["paper_ids"]
    produces: list[str] = ["artifact_response"]
    metadata: dict = {
        "description": "Create a PAPER_COLLECTION artifact",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = ArtifactStage(artifact_service=kwargs["artifact_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class TimelinePlugin(PipelinePlugin):
    """Record pipeline completion in the investigation timeline."""

    _name = "timeline"
    consumes: list[str] = []
    produces: list[str] = ["timeline_recorded"]
    metadata: dict = {
        "description": "Record pipeline completion in the investigation timeline",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = TimelineStage(timeline_service=kwargs["timeline_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class ValidatePlugin(PipelinePlugin):
    """Run deterministic validation on retrieved papers."""

    _name = "validate"
    consumes: list[str] = ["papers"]
    produces: list[str] = ["validated_papers"]
    metadata: dict = {
        "description": "Run deterministic validation on retrieved papers",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = ValidateStage(validation_service=kwargs["validation_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class ExtractPlugin(PipelinePlugin):
    """Run LLM-based knowledge extraction on persisted papers."""

    _name = "extract"
    consumes: list[str] = ["paper_ids"]
    produces: list[str] = ["extracted_knowledge_ids"]
    metadata: dict = {
        "description": "Run LLM-based knowledge extraction on persisted papers",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = ExtractStage(extraction_service=kwargs["extraction_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class AnalyzePlugin(PipelinePlugin):
    """Run deterministic cross-paper analysis on extracted knowledge."""

    _name = "analyze"
    consumes: list[str] = ["extracted_knowledge_ids"]
    produces: list[str] = ["research_landscape"]
    metadata: dict = {
        "description": "Run deterministic cross-paper analysis on extracted knowledge",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = AnalyzeStage(analysis_service=kwargs["analysis_service"])

    async def execute(self, context):
        return await self._inner.execute(context)


class GapDetectionPlugin(PipelinePlugin):
    """Run deterministic rule-based research gap detection."""

    _name = "gap_detection"
    consumes: list[str] = []
    produces: list[str] = ["research_gap_report"]
    metadata: dict = {
        "description": "Run deterministic rule-based research gap detection",
    }

    def __init__(self, **kwargs) -> None:
        self._inner = GapDetectionStage(
            gap_detection_service=kwargs["gap_detection_service"],
        )

    async def execute(self, context):
        return await self._inner.execute(context)
