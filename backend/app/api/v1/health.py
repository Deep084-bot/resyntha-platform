"""Legacy health endpoints — redirects to app.health.routes.

All new code should import from ``app.health.routes`` directly.
This module exists only to avoid breaking existing imports during
the transition.
"""

from app.health.routes import router

__all__ = ["router"]
