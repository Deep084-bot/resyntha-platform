"""Retry policy for pipeline stages.

Encapsulates how many times a stage should be retried and how long
to wait between attempts.  Separate from ``PipelineRunner`` so that
different stages can have different policies in the future.
"""

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Controls retry behaviour for a failing stage.

    ``max_retries``
        Maximum number of *additional* attempts after the first failure.
        ``0`` means no retries — the stage runs once.

    ``backoff_seconds``
        Base wait time between retries in seconds.

    ``exponential_backoff``
        When ``True`` the wait time doubles after each attempt:
        ``wait = backoff_seconds * 2 ** (attempt - 1)``.
    """

    max_retries: int = 2
    backoff_seconds: float = 1.0
    exponential_backoff: bool = True
