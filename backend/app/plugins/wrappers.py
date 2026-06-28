"""Wrapper plugins that delegate to existing pipeline stages.

Each plugin class internally instantiates the corresponding stage
and forwards ``execute()`` calls to it.  Business logic lives in
the stages — never duplicated here.
"""

from app.pipeline.stages import (
    ArtifactStage,
    PersistStage,
    RetrieveStage,
    TimelineStage,
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
