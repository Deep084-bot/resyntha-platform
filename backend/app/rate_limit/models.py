"""Data models for rate limiting decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RateLimitResult:
    """Outcome of a rate limit check.

    Attributes
    ----------
    allowed:
        Whether the request should proceed.
    limit:
        Maximum requests allowed in the window.
    remaining:
        Requests remaining in the current window.
    reset_at:
        Unix timestamp when the window resets.
    retry_after:
        Seconds until the window resets (0 when allowed).
    """

    allowed: bool
    limit: int
    remaining: int = 0
    reset_at: float = 0.0
    retry_after: int = 0


RATE_LIMIT_EXCEEDED_RESPONSE: dict = {
    "type": "about:blank",
    "title": "Too Many Requests",
    "status": 429,
    "detail": "Rate limit exceeded. Please wait before retrying.",
}
