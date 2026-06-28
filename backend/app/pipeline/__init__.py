"""Pipeline engine — a generic, reusable execution framework.

This package provides the primitives for composing and running
multi-stage research pipelines.  It is intentionally free of any
domain logic (retrieval, extraction, etc.) so that every future
pipeline stage can use it without modification.

Main components
---------------
``PipelineContext``
    Shared state object passed through every stage of a pipeline run.

``PipelineResult``
    Enum returned by each stage to signal success, failure, skip,
    or retry.

``PipelineStage``
    Abstract base class that every stage must subclass.

``PipelineDefinition``
    Named, validated collection of stages — the public entry point.

``PipelineRunner``
    Orchestrator that executes stages sequentially with retry support.

``RetryPolicy``
    Configuration for how many times and how fast to retry a stage.

``PipelineException`` (and subclasses)
    Exception hierarchy for pipeline-specific errors.
"""

from app.pipeline.context import PipelineContext
from app.pipeline.definition import PipelineDefinition
from app.pipeline.exceptions import (
    PipelineException,
    RetryExceededException,
    StageExecutionException,
)
from app.pipeline.recorder import StageRecorder
from app.pipeline.result import PipelineResult
from app.pipeline.retry import RetryPolicy
from app.pipeline.runner import PipelineRunner
from app.pipeline.stage import PipelineStage

__all__ = [
    "PipelineContext",
    "PipelineDefinition",
    "PipelineException",
    "PipelineResult",
    "PipelineRunner",
    "PipelineStage",
    "RetryExceededException",
    "RetryPolicy",
    "StageExecutionException",
    "StageRecorder",
]
