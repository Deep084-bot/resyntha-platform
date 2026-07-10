"""Request-logging middleware.

Measures request duration and emits structured log entries on
request completion.  Unhandled exceptions are logged with full
context before being re-raised.
"""

from __future__ import annotations

import time
import traceback

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.context import (
    RequestContext,
    clear_request_context,
    set_request_context,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """ASGI middleware that logs request completion and errors."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.get("state", {})
        request_id = state.get("request_id", "")

        client_ip = scope.get("client", ("", 0))[0]
        method = scope.get("method", "")
        path = scope.get("path", "")
        user_agent = ""
        for name, value in scope.get("headers", []):
            if name == b"user-agent":
                user_agent = value.decode("utf-8", errors="replace")
                break

        ctx = RequestContext(
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        set_request_context(ctx)

        start = time.monotonic()
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "request_exception",
                request_id=request_id,
                method=method,
                path=path,
                status_code=500,
                duration_ms=elapsed_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                error_type=traceback.format_exc(),
            )
            clear_request_context()
            raise

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "request_completed",
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=elapsed_ms,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        clear_request_context()
