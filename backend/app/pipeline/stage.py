"""Abstract pipeline stage.

Every phase of a research investigation — retrieval, extraction,
comparison, trend analysis, gap detection, idea generation,
report writing — is a ``PipelineStage``.  This abstraction lets
the ``PipelineRunner`` treat them uniformly.

To create a new stage, subclass ``PipelineStage`` and implement
``name()`` and ``execute()``.  Set ``consumes``, ``produces``, and
``metadata`` as class attributes so that ``PipelineDefinition`` can
validate the stage graph before execution.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult


class PipelineStage(ABC):
    """Unit of work that can be composed into a pipeline."""

    #: Artifact keys this stage expects to find in ``PipelineContext``.
    #: Used by ``PipelineDefinition.validate()`` to catch missing
    #: dependencies before execution.
    consumes: list[str] = []

    #: Artifact keys this stage writes into ``PipelineContext``.
    #: Declaring outputs lets downstream stages and the definition
    #: validator understand the data flow.
    produces: list[str] = []

    #: Static metadata describing the stage (e.g. human-readable
    #: description, version).  Not used by the runner — available
    #: for tooling and observability.
    metadata: dict[str, Any] = {}

    @abstractmethod
    def name(self) -> str:
        """Human-readable stage identifier (e.g. ``"retrieve"``, ``"extract"``).

        Used by the runner for logging, error tracking, and context
        updates.  Should be a short, kebab-case string.
        """

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute the stage's work and return a result.

        Receives the shared ``PipelineContext`` which carries the
        investigation id, artifacts from earlier stages, and runtime
        metadata.  Store durable outputs in ``context.artifacts``.

        Raise ``StageExecutionException`` for problems that may be
        transient (the runner can retry).  Return ``FAILED`` for
        unrecoverable errors.
        """
