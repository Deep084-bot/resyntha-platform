"""Per-endpoint rate-limit overrides via ``@rate_limit()``.

Since ASGI middleware cannot reliably inspect route metadata at
runtime, the decorator registers the override in a global registry
that the middleware consults.  The decorand *must* supply the HTTP
method and URL path so the registry can be populated.

Usage::

    from app.rate_limit import rate_limit

    @router.get("/my-endpoint")
    @rate_limit("GET", "/my-endpoint", limit=50, window=60)
    async def my_handler():
        ...

For convenience, a ``rate_limit_on(limit, window)`` shortcut is
provided that can be paired with a separate ``register()`` call
after the route is registered (see ``app/api/v1/__init__.py``).
"""

from __future__ import annotations

from app.rate_limit.middleware import register_override

_RATE_LIMIT_ATTR = "_rate_limit_config"


def rate_limit(
    method: str = "",
    path: str = "",
    limit: int = 120,
    window: int = 60,
):
    """Override the default rate-limit policy for the decorated endpoint.

    Parameters
    ----------
    method:
        HTTP method (GET, POST, etc.).
    path:
        URL path to override (e.g. "/api/v1/my-endpoint").
    limit:
        Maximum requests allowed in the *window*.
    window:
        Time window in seconds.

    When ``method`` and ``path`` are both non-empty the override is
    registered immediately in the middleware's override registry.
    """
    cfg = {"limit": limit, "window": window}

    if method and path:
        register_override(method, path, limit, window)

    def decorator(func):
        setattr(func, _RATE_LIMIT_ATTR, cfg)
        return func

    return decorator
