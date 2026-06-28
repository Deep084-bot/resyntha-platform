"""Low-level structlog configuration.

Runs once at import time to set up structured JSON formatting with
timestamp, log level, module name, and event name.  All application
code obtains loggers through ``observability.logger.get_logger``
rather than calling ``structlog.get_logger`` directly.
"""

import logging
import sys

import structlog
import structlog.processors
import structlog.stdlib


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            (
                structlog.dev.ConsoleRenderer()
                if __debug__
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    