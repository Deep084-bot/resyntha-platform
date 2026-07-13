"""Pipeline execution result.

Every stage returns a ``PipelineResult`` to tell the runner what to do
next.  Keeping results as an enum (rather than boolean flags) makes the
protocol explicit and extensible.
"""

from enum import StrEnum


class PipelineResult(StrEnum):
    """Outcome of a single pipeline stage.

    ``SUCCESS``
        The stage completed normally; proceed to the next stage.

    ``PARTIAL_SUCCESS``
        The stage completed with some failures; proceed to the next
        stage.  The runner may use this to inform the overall pipeline
        result.

    ``FAILED``
        The stage encountered an unrecoverable error; the runner should
        stop the pipeline.

    ``SKIPPED``
        The stage determined that its work was unnecessary (e.g. the
        data already exists); proceed to the next stage.

    ``RETRY``
        The stage could not complete but may succeed after a back-off;
        the runner should retry according to the configured policy.
    """

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"
