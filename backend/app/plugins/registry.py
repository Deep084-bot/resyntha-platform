"""Pipeline registry — the single source of truth for named pipelines.

``PipelineRegistry`` stores named pipeline definitions as ordered
lists of plugin classes.  Callers ask for a pipeline by name and
receive a ready-to-run ``PipelineDefinition``, completely decoupled
from which stages make up the pipeline.

Usage::

    pipeline = registry.get_pipeline(
        "retrieval",
        stage_recorder=stage_service,
        retrieval_service=retrieval_service,
        paper_service=paper_service,
        artifact_service=artifact_service,
        timeline_service=timeline_service,
    )
    final_context = await pipeline.run(context)
"""

from collections.abc import Sequence

from app.pipeline.definition import PipelineDefinition
from app.plugins.base import PipelinePlugin
from app.plugins.wrappers import (
    AnalyzePlugin,
    ArtifactPlugin,
    ExtractPlugin,
    GapDetectionPlugin,
    IntelligencePlugin,
    PersistPlugin,
    RetrievePlugin,
    TimelinePlugin,
    ValidatePlugin,
)


class PipelineRegistry:
    """Maps pipeline names to ordered lists of plugin classes.

    Register a pipeline once; the worker requests it by name and
    never needs to know the stage composition.
    """

    def __init__(self) -> None:
        self._pipelines: dict[str, list[type[PipelinePlugin]]] = {}

    def register(
        self,
        name: str,
        plugin_classes: Sequence[type[PipelinePlugin]],
    ) -> None:
        """Register a named pipeline.

        ``plugin_classes`` are ordered — they execute in the given
        sequence.
        """
        self._pipelines[name] = list(plugin_classes)

    def get_pipeline(self, name: str, **kwargs: object) -> PipelineDefinition:
        """Return a ``PipelineDefinition`` for the named pipeline.

        All extra ``**kwargs`` are forwarded to each plugin's
        ``__init__``, except ``stage_recorder`` and ``retry_policy``
        which are passed to ``PipelineDefinition``.
        """
        plugin_classes = self._pipelines.get(name)
        if plugin_classes is None:
            msg = f"Pipeline '{name}' is not registered"
            raise KeyError(msg)

        stage_recorder = kwargs.pop("stage_recorder", None)

        plugins = [cls(**kwargs) for cls in plugin_classes]

        return PipelineDefinition(
            name=name,
            stages=plugins,
            stage_recorder=stage_recorder,
        )


# Module-level singleton, pre-loaded with the retrieval pipeline.
registry = PipelineRegistry()
registry.register(
    "retrieval",
    [
        RetrievePlugin,
        ValidatePlugin,
        PersistPlugin,
        ExtractPlugin,
        AnalyzePlugin,
        IntelligencePlugin,
        GapDetectionPlugin,
        ArtifactPlugin,
        TimelinePlugin,
    ],
)
