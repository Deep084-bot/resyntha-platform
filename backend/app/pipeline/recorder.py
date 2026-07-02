"""Stage recorder protocol.

The ``StageRecorder`` protocol defines the interface for recording
stage lifecycle events.  ``PipelineRunner`` calls into a recorder
(if one is provided) so that callers can persist or observe stage
progress without coupling the pipeline engine to any specific
storage backend.

Implementations live in the application layer (e.g. the execution
module's ``ExecutionStageService``).
"""

from typing import Protocol
from uuid import UUID


class StageRecorder(Protocol):
    """Interface for recording stage lifecycle events.

    ``record_started`` is called *before* each stage attempt.
    ``record_completed`` / ``record_failed`` are called *after*
    the attempt completes.
    """

    async def record_started(
        self,
        execution_id: UUID,
        stage_name: str,
        attempt: int,
    ) -> None:
        """Record that a stage attempt has begun."""

    async def record_completed(
        self,
        execution_id: UUID,
        stage_name: str,
        metadata: dict | None = None,
    ) -> None:
        """Record that a stage attempt completed successfully.

        When *metadata* is provided the stage is recorded as
        ``PARTIAL_SUCCESS`` and the metadata is persisted in the
        stage's JSONB column.
        """

    async def record_failed(
        self,
        execution_id: UUID,
        stage_name: str,
        error_message: str,
    ) -> None:
        """Record that a stage attempt failed."""
