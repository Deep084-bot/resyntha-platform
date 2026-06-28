"""Pipeline plugin base class.

``PipelinePlugin`` mirrors the ``PipelineStage`` API exactly so that
``PipelineDefinition`` and ``PipelineRunner`` can treat plugins and
stages interchangeably via duck typing.

Plugin subclasses wrap an existing ``PipelineStage`` instance and
delegate ``execute()`` to it — business logic is never duplicated.
"""

from typing import Any

from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult


class PipelinePlugin:
    """Lightweight plugin interface.

    Subclasses set ``_name``, ``consumes``, ``produces`` as class
    attributes and implement ``execute()``, typically by delegating
    to an existing ``PipelineStage``.
    """

    #: Plugin identifier (e.g. ``"retrieve"``, ``"persist"``).
    _name: str = ""

    #: Artifact keys this plugin expects in ``PipelineContext``.
    consumes: list[str] = []

    #: Artifact keys this plugin writes into ``PipelineContext``.
    produces: list[str] = []

    #: Static metadata (description, version, etc.).
    metadata: dict[str, Any] = {}

    def name(self) -> str:
        """Return the plugin identifier.

        Mirrors ``PipelineStage.name()``.
        """
        return self._name

    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute the plugin's work.

        Must be overridden by subclasses.
        """
        raise NotImplementedError
