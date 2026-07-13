"""Request-size limit middleware.

Rejects requests whose body exceeds a configurable threshold.
Handles both ``Content-Length`` and chunked-transfer bodies.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.observability.logger import get_logger

logger = get_logger(__name__)

PAYLOAD_TOO_LARGE_BODY = json.dumps(
    {
        "error": "payload_too_large",
        "message": "Request body exceeds the maximum allowed size",
    }
).encode()


async def _send_413(send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/problem+json"),
            ],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": PAYLOAD_TOO_LARGE_BODY,
        }
    )


class RequestSizeLimitMiddleware:
    """ASGI middleware that enforces a maximum request-body size."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        max_size = settings.MAX_REQUEST_SIZE

        # --- Check Content-Length header (fast path) ---
        headers = dict(scope.get("headers", []) or [])
        content_length = headers.get(b"content-length")

        if content_length is not None:
            try:
                size = int(content_length)
            except (ValueError, TypeError):
                size = 0
            if size > max_size:
                logger.warning(
                    "oversized_request",
                    content_length=size,
                    max_size=max_size,
                    path=scope.get("path", ""),
                    method=scope.get("method", ""),
                )
                await _send_413(send)
                return

        # --- Intercept receive to count bytes (covers chunked) ---
        received = 0

        async def counting_receive() -> dict:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                body: bytes = message.get("body", b"") or b""
                received += len(body)
                if received > max_size:
                    logger.warning(
                        "oversized_request_chunked",
                        received=received,
                        max_size=max_size,
                        path=scope.get("path", ""),
                        method=scope.get("method", ""),
                    )
                    raise _SizeLimitExceeded()
            return message

        try:
            await self.app(scope, counting_receive, send)
        except _SizeLimitExceeded:
            await _send_413(send)


class _SizeLimitExceeded(Exception):  # noqa: N818
    """Internal signal raised when the body exceeds the size limit."""
