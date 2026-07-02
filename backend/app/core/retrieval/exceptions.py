"""Provider-independent retrieval exceptions.

Every exception in this module inherits from ``RetrievalError`` so
that callers can catch all retrieval-related errors with a single
except clause.

Providers translate their SDK/HTTP exceptions into these
provider-independent types before raising them to the business layer.
"""


class RetrievalError(Exception):
    """Base exception for all retrieval-layer errors.

    Attributes
    ----------
    response_time_ms:
        Provider response time in milliseconds (0 if unknown).
    """

    def __init__(self, message: str, response_time_ms: float = 0.0) -> None:
        self.response_time_ms = response_time_ms
        super().__init__(message)


class RetrievalConnectionError(RetrievalError):
    """Raised when a connection to the provider cannot be established.

    Covers DNS failures, connection refused, SSL errors, etc.
    """


class RetrievalRateLimitError(RetrievalError):
    """Raised when the provider returns a rate-limit response (HTTP 429)."""


class RetrievalTimeoutError(RetrievalError):
    """Raised when the provider request times out."""


class RetrievalAPIError(RetrievalError):
    """Raised when the provider returns a non-retriable API error.

    Covers 5xx server errors, unexpected response formats, and
    unrecoverable client errors.
    """
