"""Pipeline-specific exceptions.

These let stages and the runner signal execution problems without
leaking implementation details to callers.  Every exception in this
module inherits from ``PipelineException`` so that top-level handlers
can catch them with a single ``except PipelineException``.
"""


class PipelineException(Exception):
    """Base exception for all pipeline errors."""


class StageExecutionException(PipelineException):
    """Raised by a stage when it cannot complete its work.

    The runner catches this, records the error in the context, and
    either retries (if the retry policy allows) or marks the stage
    as failed.
    """


class RetryExceededException(PipelineException):
    """Raised when a stage has exhausted its allowed retries.

    The runner converts this into a ``FAILED`` result and stops the
    pipeline.
    """
