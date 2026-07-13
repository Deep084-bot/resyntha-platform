"""Application-level logger factory.

Every module in the codebase should import ``get_logger`` from this
module instead of calling ``structlog.get_logger`` directly.  This
gives a single point of control for log-enrichment (e.g. correlation
IDs, tenant context) in the future.
"""

import structlog


def get_logger(name: str):
    return structlog.get_logger(name)
