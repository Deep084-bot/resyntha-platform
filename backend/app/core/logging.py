"""Low-level structlog configuration.

Runs once at import time to set up structured JSON formatting with
timestamp, log level, module name, and event name.  All application
code obtains loggers through ``observability.logger.get_logger``
rather than calling ``structlog.get_logger`` directly.
"""

import structlog
import structlog.processors
import structlog.stdlib


def configure_logging() -> None:
    """Apply global structlog processor chain.

    Safe to call multiple times — only the first call has an effect.
    """
    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if __debug__
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
