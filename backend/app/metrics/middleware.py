"""ASGI middleware that collects HTTP request metrics.

Incoming Request
       │
       ▼
Increment active_requests
       │
       ▼
Call handler
       │
       ▼
Record latency histogram
       │
       ▼
Increment request counter (method, endpoint, status)
       │
       ▼
Decrement active_requests
"""

from __future__ import annotations

import time

from starlette.types import ASGIApp, Receive, Scope, Send

from app.metrics.service import get_metrics_service


class MetricsMiddleware:
    """ASGI middleware that observes HTTP request metrics."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        metrics = get_metrics_service()
        method = scope.get("method", "")
        path = scope.get("path", "")
        metrics.http_requests_active.inc()
        start = time.monotonic()
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.monotonic() - start
            metrics.http_requests_active.dec()
            metrics.http_request_duration_seconds.observe(elapsed, method=method, endpoint=path)
            metrics.http_requests_total.inc(
                method=method,
                endpoint=path,
                status=str(status_code),
            )
