"""Application-level logger factory.

Every module in the codebase should import ``get_logger`` from this
module instead of calling ``structlog.get_logger`` directly.  This
gives a single point of control for log-enrichment (e.g. correlation
IDs, tenant context) in the future.
"""

import structlog
from structlog.stdlib import BoundLogger


def get_logger(name: str) -> BoundLogger:  # type: ignore[type-arg]
    """Return a structured logger bound to *name* (typically ``__name__``).

    The returned logger writes JSON-formatted records with timestamp,
    log level, module name, and event name.
    """
    return structlog.get_logger(name)
