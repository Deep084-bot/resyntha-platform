"""Request- and worker-scoped context using ``contextvars``.

Provides ``RequestContext`` and ``WorkerContext`` dataclasses that
flow with the current async execution scope.  Middleware and log
processors read from these to enrich log events without passing
state manually.
"""

from __future__ import annotations

import time
from contextvars import ContextVar
from dataclasses import dataclass, field

# ── Request Context ──────────────────────────────────────────────────────────


@dataclass
class RequestContext:
    """Contextual information for the current HTTP request."""

    request_id: str = ""
    method: str = ""
    path: str = ""
    client_ip: str = ""
    user_agent: str = ""
    start_time: float = field(default_factory=time.monotonic)


_request_ctx: ContextVar[RequestContext | None] = ContextVar(
    "request_context",
    default=None,
)


def get_request_context() -> RequestContext | None:
    return _request_ctx.get()


def set_request_context(ctx: RequestContext) -> None:
    _request_ctx.set(ctx)


def clear_request_context() -> None:
    _request_ctx.set(None)


# ── Worker Context ───────────────────────────────────────────────────────────


@dataclass
class WorkerContext:
    """Contextual information for a background worker job."""

    investigation_id: str = ""
    execution_id: str = ""
    stage: str = ""
    request_id: str = ""


_worker_ctx: ContextVar[WorkerContext | None] = ContextVar(
    "worker_context",
    default=None,
)


def get_worker_context() -> WorkerContext | None:
    return _worker_ctx.get()


def set_worker_context(ctx: WorkerContext) -> None:
    _worker_ctx.set(ctx)


def clear_worker_context() -> None:
    _worker_ctx.set(None)
