"""LLM-specific exceptions.

Every exception in this module inherits from ``LLMError`` so that
callers can catch all LLM-related errors with a single except clause.
"""


class LLMError(Exception):
    """Base exception for all LLM-layer errors."""


class LLMParsingError(LLMError):
    """Raised when the LLM response cannot be parsed as valid JSON.

    Attributes
    ----------
    raw:
        The original response text returned by the provider.
    sanitized:
        The text after whitespace / fence removal but before JSON parsing.
    finish_reason:
        The ``finish_reason`` from the provider response, if available.
    parse_exception:
        The underlying exception from the failed ``json.loads()`` call.
    """

    def __init__(
        self,
        message: str,
        raw: str = "",
        sanitized: str = "",
        finish_reason: str | None = None,
        parse_exception: Exception | None = None,
    ) -> None:
        self.raw = raw
        self.sanitized = sanitized
        self.finish_reason = finish_reason
        self.parse_exception = parse_exception
        super().__init__(message)
