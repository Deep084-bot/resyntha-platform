"""Concrete pipeline stages for the Resyntha platform.

Each stage inherits ``PipelineStage``, declares its ``consumes``
and ``produces`` artifact keys, and implements ``execute()`` with
a single responsibility.

Stages in this package know about domain services (retrieval,
persistence, artifacts, timeline) but contain no orchestration
logic — that belongs in ``PipelineDefinition`` + ``PipelineRunner``.
"""

from app.pipeline.stages.analyze import AnalyzeStage
from app.pipeline.stages.artifact import ArtifactStage
from app.pipeline.stages.extract import ExtractStage
from app.pipeline.stages.gap_detection import GapDetectionStage
from app.pipeline.stages.intelligence import IntelligenceStage
from app.pipeline.stages.persist import PersistStage
from app.pipeline.stages.retrieve import RetrieveStage
from app.pipeline.stages.timeline import TimelineStage
from app.pipeline.stages.validate import ValidateStage

__all__ = [
    "AnalyzeStage",
    "ArtifactStage",
    "ExtractStage",
    "GapDetectionStage",
    "IntelligenceStage",
    "PersistStage",
    "RetrieveStage",
    "TimelineStage",
    "ValidateStage",
]
