"""ASGI middleware that injects security and CSP response headers.

Middleware order: installed *after* CORS (outer) so that hardened
headers are the last set applied before the response goes out.
"""

from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.observability.logger import get_logger
from app.security.config import build_security_headers

logger = get_logger(__name__)


class SecurityHeadersMiddleware:
    """Injects security-related response headers on every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        if not settings.SECURITY_HEADERS_ENABLED:
            await self.app(scope, receive, send)
            return

        headers = build_security_headers()

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                msg_headers = MutableHeaders(scope=message)
                for name, value in headers.items():
                    msg_headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_wrapper)
