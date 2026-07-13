"""Rate-limiting ASGI middleware with per-endpoint override support.

Incoming Request
       │
       ▼
 Identify Client
       │
       ▼
 Lookup Policy
       │
       ▼
 Check Limit
       │
   ┌───┴────┐
   │        │
  Yes       No
   │        │
   ▼        ▼
Handler    429 + headers
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import Settings, get_settings
from app.observability.logger import get_logger
from app.rate_limit.models import RATE_LIMIT_EXCEEDED_RESPONSE, RateLimitResult
from app.rate_limit.service import RateLimitService

logger = get_logger(__name__)

# Paths that bypass rate limiting entirely.
UNLIMITED_PATHS = frozenset(
    {
        "/api/v1/live",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/metrics/info",
    }
)

# Sentinel attribute name for per-endpoint overrides.
RATE_LIMIT_ATTR = "_rate_limit_config"

# Registry for explicit per-endpoint overrides.
# Maps (method, exact_path) -> {"limit": int, "window": int}
_override_registry: dict[tuple[str, str], dict] = {}


def register_override(
    method: str,
    path: str,
    limit: int,
    window: int,
) -> None:
    """Register a per-endpoint rate-limit override."""
    _override_registry[(method.upper(), path)] = {"limit": limit, "window": window}


def _resolve_policy(
    method: str,
    path: str,
    settings: Settings,
) -> tuple[int, int]:
    """Return ``(limit, window)`` for the given request.

    Checks the override registry first, then falls back to
    path-based defaults.
    """
    # Check for explicit per-endpoint override
    override = _override_registry.get((method, path))
    if override is not None:
        return override["limit"], override["window"]

    if path in UNLIMITED_PATHS:
        return 0, 0  # 0 limit = unlimited

    if method == "POST" and path.rstrip("/").endswith("/retrieve"):
        return settings.RUN_RATE_LIMIT, settings.RATE_LIMIT_WINDOW

    if method == "POST" and path.rstrip("/") == f"{settings.API_V1_PREFIX}/investigations":
        return settings.INVESTIGATION_RATE_LIMIT, settings.RATE_LIMIT_WINDOW

    if "/copilot" in path and "/chat" in path:
        return settings.COPILOT_RATE_LIMIT, settings.RATE_LIMIT_WINDOW

    return settings.DEFAULT_RATE_LIMIT, settings.RATE_LIMIT_WINDOW


def _identify_client(scope: Scope) -> str:
    """Return a stable client identifier for rate limiting.

    Uses user id from ``scope["state"]`` when authentication is
    present (future), otherwise falls back to client IP.
    """
    state = scope.get("state") or {}
    user_id = state.get("user_id")
    if user_id:
        return f"user:{user_id}"
    client = scope.get("client") or ("unknown", 0)
    return f"ip:{client[0]}"


class RateLimitMiddleware:
    """ASGI middleware that enforces per-client rate limits."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._service: RateLimitService | None = None

    def _service_instance(self) -> RateLimitService:
        if self._service is None:
            self._service = RateLimitService()
        return self._service

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        limit, window = _resolve_policy(method, path, settings)

        # Unlimited path
        if limit == 0:
            await self.app(scope, receive, send)
            return

        client_key = _identify_client(scope)
        svc = self._service_instance()
        result = await svc.check(client_key, limit=limit, window=window)

        if result.allowed:
            await self._send_with_headers(scope, receive, send, result)
        else:
            await self._send_429(scope, send, result)

    async def _send_with_headers(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        result: RateLimitResult,
    ) -> None:
        """Forward the request, adding rate-limit headers to the response."""

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.extend(
                    [
                        (b"X-RateLimit-Limit", str(result.limit).encode()),
                        (b"X-RateLimit-Remaining", str(result.remaining).encode()),
                        (b"X-RateLimit-Reset", str(int(result.reset_at)).encode()),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

    async def _send_429(
        self,
        scope: Scope,
        send: Send,
        result: RateLimitResult,
    ) -> None:
        body = json.dumps(RATE_LIMIT_EXCEEDED_RESPONSE).encode()
        headers = [
            (b"content-type", b"application/problem+json"),
            (b"X-RateLimit-Limit", str(result.limit).encode()),
            (b"X-RateLimit-Remaining", b"0"),
            (b"X-RateLimit-Reset", str(int(result.reset_at)).encode()),
            (b"Retry-After", str(result.retry_after).encode()),
        ]
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )
