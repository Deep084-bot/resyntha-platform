"""Request timeout middleware.

Wraps the ASGI call chain in ``asyncio.wait_for`` and returns a
504 Gateway Timeout response when the configured threshold is
exceeded.  Catches the timeout exception so that the worker
process is never killed.
"""

from __future__ import annotations

import asyncio
import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.observability.logger import get_logger

logger = get_logger(__name__)

GATEWAY_TIMEOUT_BODY = json.dumps({
    "error": "gateway_timeout",
    "message": "Request timed out processing",
}).encode()


async def _send_504(send: Send) -> None:
    await send({
        "type": "http.response.start",
        "status": 504,
        "headers": [
            (b"content-type", b"application/problem+json"),
        ],
    })
    await send({
        "type": "http.response.body",
        "body": GATEWAY_TIMEOUT_BODY,
    })


class TimeoutMiddleware:
    """ASGI middleware that enforces a per-request wall-clock timeout."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        timeout = settings.REQUEST_TIMEOUT_SECONDS

        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "request_timeout",
                path=scope.get("path", ""),
                method=scope.get("method", ""),
                timeout_seconds=timeout,
            )
            await _send_504(send)
