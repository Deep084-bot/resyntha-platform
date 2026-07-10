"""Request-ID middleware.

Generates or reuses a UUIDv4 request ID for every incoming HTTP
request.  The ID is stored in ``request.state.request_id`` and
returned as the ``X-Request-ID`` response header.
"""

from __future__ import annotations

import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    """ASGI middleware that attaches a unique request ID to each request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        existing = headers.get("x-request-id", "")

        if existing and self._is_valid_uuid(existing):
            request_id = existing
        else:
            request_id = str(uuid.uuid4())
            headers["x-request-id"] = request_id

        scope["state"] = {**(scope.get("state") or {}), "request_id": request_id}

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                msg_headers = MutableHeaders(scope=message)
                msg_headers.setdefault("X-Request-ID", request_id)
            await send(message)

        await self.app(scope, receive, send_wrapper)

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False
