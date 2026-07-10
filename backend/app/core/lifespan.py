"""Legacy lifespan adapter.

Redirects to the canonical lifespan in ``app.bootstrap.lifespan``.
All new code should import from ``app.bootstrap.lifespan`` directly.
"""

from app.bootstrap.lifespan import lifespan

__all__ = ["lifespan"]
