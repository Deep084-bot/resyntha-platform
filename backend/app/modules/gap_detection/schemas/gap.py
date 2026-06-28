"""API response schemas for gap detection.

Currently re-exports domain models. Exists as a seam for future
divergence between internal and API representations.
"""

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
    GapSummary,
    ResearchGapReport,
)

__all__ = [
    "Evidence",
    "Gap",
    "GapCategory",
    "GapSeverity",
    "GapSummary",
    "ResearchGapReport",
]
