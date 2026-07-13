"""Low-level structlog configuration.

Runs once during application startup to set up structured logging
with timestamp, log level, module name, and event name.  The output
format (console vs JSON) and the inclusion of request- and worker-
context fields are driven by configuration.
"""

from __future__ import annotations

import logging
import sys

import structlog
import structlog.processors
import structlog.stdlib

from app.config import get_settings
from app.core.context import get_request_context, get_worker_context


def add_context(
    logger: structlog.stdlib.BoundLogger,
    method_name: str,
    event_dict: dict,
) -> dict:
    """Inject request- and worker-context fields into every log event.

    Reads the current ``RequestContext`` and ``WorkerContext`` from
    ``contextvars`` and enriches the event with their fields when
    available.  Outside a context no extra fields are added.
    """
    req_ctx = get_request_context()
    if req_ctx is not None:
        if req_ctx.request_id:
            event_dict["request_id"] = req_ctx.request_id
        if req_ctx.method:
            event_dict["method"] = req_ctx.method
        if req_ctx.path:
            event_dict["path"] = req_ctx.path
        if req_ctx.client_ip:
            event_dict["client_ip"] = req_ctx.client_ip
        if req_ctx.user_agent:
            event_dict["user_agent"] = req_ctx.user_agent

    wkr_ctx = get_worker_context()
    if wkr_ctx is not None:
        if wkr_ctx.execution_id:
            event_dict["execution_id"] = wkr_ctx.execution_id
        if wkr_ctx.investigation_id:
            event_dict["investigation_id"] = wkr_ctx.investigation_id
        if wkr_ctx.stage:
            event_dict["stage"] = wkr_ctx.stage
        if wkr_ctx.request_id:
            event_dict.setdefault("request_id", wkr_ctx.request_id)

    return event_dict


def configure_logging() -> None:
    settings = get_settings()

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    use_json = settings.LOG_FORMAT == "json"

    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_context,
            (structlog.processors.JSONRenderer() if use_json else structlog.dev.ConsoleRenderer()),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
