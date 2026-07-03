"""Intelligence aggregation layer.

Transforms AnalysisResults into a LandscapeResult — a typed, structured
view of the entire research landscape.  No graph traversal, no LLM,
no database access.
"""

from app.modules.intelligence.aggregation.aggregator import LandscapeAggregator
from app.modules.intelligence.aggregation.models import (
    CollaborationSection,
    DatasetSection,
    DiversityMetrics,
    InstitutionEntry,
    InstitutionSection,
    LandscapeResult,
    MethodologyEntry,
    MethodologySection,
    NetworkSection,
    Observation,
    OverviewSection,
    StatisticsSection,
    TechnologySection,
    TemporalSection,
)

__all__ = [
    "CollaborationSection",
    "DatasetSection",
    "DiversityMetrics",
    "InstitutionEntry",
    "InstitutionSection",
    "LandscapeAggregator",
    "LandscapeResult",
    "MethodologyEntry",
    "MethodologySection",
    "NetworkSection",
    "Observation",
    "OverviewSection",
    "StatisticsSection",
    "TechnologySection",
    "TemporalSection",
]
