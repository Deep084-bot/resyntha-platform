"""Concrete pipeline stages for the Resyntha platform.

Each stage inherits ``PipelineStage``, declares its ``consumes``
and ``produces`` artifact keys, and implements ``execute()`` with
a single responsibility.

Stages in this package know about domain services (retrieval,
persistence, artifacts, timeline) but contain no orchestration
logic — that belongs in ``PipelineDefinition`` + ``PipelineRunner``.
"""

from app.pipeline.stages.artifact import ArtifactStage
from app.pipeline.stages.persist import PersistStage
from app.pipeline.stages.retrieve import RetrieveStage
from app.pipeline.stages.timeline import TimelineStage

__all__ = [
    "ArtifactStage",
    "PersistStage",
    "RetrieveStage",
    "TimelineStage",
]
