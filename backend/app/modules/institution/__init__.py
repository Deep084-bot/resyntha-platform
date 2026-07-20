"""Institution Intelligence — profiles, search, ranking, trends, and comparison.

All computation is dynamic from the ResearchGraph.
No persistence, no external indices.
"""

from app.modules.institution.domain.models import (
    AuthorEntry,
    CollaborationEntry,
    EntityCount,
    InstitutionComparisonDetail,
    InstitutionIntelligence,
    InstitutionProfile,
    InstitutionRankingEntry,
    InstitutionSearchResult,
    InstitutionTrend,
    PaperEntry,
    TopicSearchResult,
    YearlyTrend,
)

__all__ = [
    "AuthorEntry",
    "CollaborationEntry",
    "EntityCount",
    "InstitutionComparisonDetail",
    "InstitutionIntelligence",
    "InstitutionProfile",
    "InstitutionRankingEntry",
    "InstitutionSearchResult",
    "InstitutionTrend",
    "PaperEntry",
    "TopicSearchResult",
    "YearlyTrend",
]
