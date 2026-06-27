"""Pipeline definition — a named, validated collection of stages.

``PipelineDefinition`` is the public entry point for running a
pipeline.  It owns the stage list, validates that every stage's
declared inputs are satisfied, and delegates execution to
``PipelineRunner``.

Separating definition from execution lets callers inspect the
pipeline graph (stages, their inputs/outputs, metadata) without
running it.
"""

from collections.abc import Sequence

from app.pipeline.context import PipelineContext
from app.pipeline.exceptions import PipelineException
from app.pipeline.retry import RetryPolicy
from app.pipeline.runner import PipelineRunner
from app.pipeline.stage import PipelineStage


class PipelineDefinition:
    """A named pipeline composed of ordered stages.

    Usage::

        definition = PipelineDefinition(
            name="retrieve",
            stages=[RetrieveStage(), PersistStage()],
        )
        context = await definition.run(ctx)
    """

    def __init__(
        self,
        name: str,
        stages: Sequence[PipelineStage],
    ) -> None:
        self._name = name
        self._stages = list(stages)

    @property
    def name(self) -> str:
        """Pipeline identifier (e.g. ``"retrieve"``, ``"extract"``)."""
        return self._name

    @property
    def stages(self) -> list[PipelineStage]:
        """Ordered list of stages in this pipeline."""
        return list(self._stages)

    def validate(self, context: PipelineContext) -> None:
        """Verify that every stage's declared inputs are satisfied.

        Walks the stage list in order, tracking which artifacts are
        available (initial context + outputs of earlier stages).
        Raises ``PipelineException`` when a stage requires an artifact
        that no earlier stage produces.
        """
        available: set[str] = set(context.artifacts.keys())

        for stage in self._stages:
            missing = set(stage.consumes) - available
            if missing:
                raise PipelineException(
                    f"Pipeline '{self._name}': stage '{stage.name()}' "
                    f"requires artifacts {missing} but they are not "
                    f"produced by any previous stage",
                )
            available.update(stage.produces)

    async def run(
        self,
        context: PipelineContext,
        retry_policy: RetryPolicy | None = None,
    ) -> PipelineContext:
        """Validate and execute the pipeline, returning the final context.

        Validates the stage graph, then delegates to ``PipelineRunner``
        for sequential execution with retry support.
        """
        self.validate(context)
        context.set_metadata("pipeline_name", self._name)
        runner = PipelineRunner(stages=self._stages, retry_policy=retry_policy)
        return await runner.run(context)
