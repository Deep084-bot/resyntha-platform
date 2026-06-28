"""Plugin architecture for the Resyntha pipeline engine.

Provides ``PipelinePlugin`` (a lightweight base class that mirrors the
``PipelineStage`` API) and ``PipelineRegistry`` for composing named
pipelines from plugin classes.

Wrapper plugins (``RetrievePlugin``, ``PersistPlugin``, etc.) delegate
to the existing pipeline stages without duplicating business logic.
"""

from app.plugins.base import PipelinePlugin
from app.plugins.registry import PipelineRegistry, registry
from app.plugins.wrappers import (
    AnalyzePlugin,
    ArtifactPlugin,
    ExtractPlugin,
    GapDetectionPlugin,
    PersistPlugin,
    RetrievePlugin,
    TimelinePlugin,
    ValidatePlugin,
)

__all__ = [
    "AnalyzePlugin",
    "ArtifactPlugin",
    "ExtractPlugin",
    "GapDetectionPlugin",
    "PipelinePlugin",
    "PipelineRegistry",
    "PersistPlugin",
    "RetrievePlugin",
    "TimelinePlugin",
    "ValidatePlugin",
    "registry",
]
