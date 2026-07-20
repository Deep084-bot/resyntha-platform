from app.modules.institution.service.comparison import (
    InstitutionComparisonService,
)
from app.modules.institution.service.ranking import (
    InstitutionAnalyticsService,
)
from app.modules.institution.service.search import InstitutionSearchService
from app.modules.institution.service.service import InstitutionProfileService

__all__ = [
    "InstitutionAnalyticsService",
    "InstitutionComparisonService",
    "InstitutionProfileService",
    "InstitutionSearchService",
]
