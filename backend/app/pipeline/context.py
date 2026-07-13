"""Pipeline execution context.

Carries all data that stages produce and consume as they execute.
The runner creates one ``PipelineContext`` per pipeline invocation and
passes it through every stage in order.

Keeping state in a single context object (rather than passing many
parameters) makes stage signatures stable as the pipeline grows.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PipelineContext:
    """Shared context for a single pipeline run.

    ``investigation_id``
        Identifies the investigation this pipeline is running for.
        Every stage receives this.

    ``execution_id``
        Identifies the execution record this pipeline run belongs to.
        Stages use it to associate artifacts and timeline events with
        the correct execution.  ``None`` when the pipeline is invoked
        outside of an execution context.

    ``current_stage``
        Set by the runner before each stage executes.  Stages can
        read it for logging or conditional behaviour.

    ``artifacts``
        Durable outputs produced by stages.  A stage stores its
        result here so that downstream stages can consume it.
        Example key: ``"paper_collection"``.

    ``metadata``
        Free-form key-value pairs that stages can read or write.
        Unlike ``artifacts`` this data is not expected to be
        persisted — it is runtime-only context (e.g. configuration
        overrides).

    ``execution_state``
        Tracks pipeline progress: which stage is running, which
        stages completed, timestamps, etc.  Written by the runner
        and read by callers after ``run()`` returns.

    ``errors``
        List of structured error records.  Each entry contains the
        stage name, human-readable message, exception detail, and
        a timestamp.

    ``metrics``
        Numeric measurements collected during execution (e.g. stage
        duration, paper count).  Useful for observability and tuning.
    """

    investigation_id: uuid.UUID
    execution_id: uuid.UUID | None = None
    current_stage: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_state: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, key: str, value: Any) -> None:
        """Store a durable output so downstream stages can consume it."""
        self.artifacts[key] = value

    def get_artifact(self, key: str, default: Any = None) -> Any:
        """Retrieve a previously stored artifact, or *default*."""
        return self.artifacts.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a runtime metadata value."""
        self.metadata[key] = value

    def add_error(
        self,
        stage: str,
        message: str,
        exception: Exception | None = None,
    ) -> None:
        """Record a structured error for the given stage."""
        self.errors.append(
            {
                "stage": stage,
                "message": message,
                "exception": f"{type(exception).__name__}: {exception}" if exception else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def record_metric(self, key: str, value: Any) -> None:
        """Record a named metric value."""
        self.metrics[key] = value

    def set_state(self, key: str, value: Any) -> None:
        """Update an execution-state field."""
        self.execution_state[key] = value
