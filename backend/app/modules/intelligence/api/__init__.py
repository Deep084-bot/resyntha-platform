"""Intelligence API layer.

Stable public interface for all external consumers.  Orchestrates
aggregation + presentation without performing either itself.
"""

from app.modules.intelligence.api.models import LandscapeResponse
from app.modules.intelligence.api.service import IntelligenceService

__all__ = [
    "IntelligenceService",
    "LandscapeResponse",
]
