from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.institution.service.comparison import (
    InstitutionComparisonService,
)
from app.modules.institution.service.ranking import (
    InstitutionAnalyticsService,
)
from app.modules.institution.service.search import InstitutionSearchService
from app.modules.institution.service.service import InstitutionProfileService
from app.modules.intelligence.graph.api.service import GraphApiService


def _make_graph_service(db: Session) -> GraphApiService:
    return GraphApiService(db)


def get_institution_profile_service(
    db: Session = Depends(get_db),
) -> InstitutionProfileService:
    return InstitutionProfileService(_make_graph_service(db))


def get_institution_search_service(
    db: Session = Depends(get_db),
) -> InstitutionSearchService:
    return InstitutionSearchService(_make_graph_service(db))


def get_institution_analytics_service(
    db: Session = Depends(get_db),
) -> InstitutionAnalyticsService:
    return InstitutionAnalyticsService(_make_graph_service(db))


def get_institution_comparison_service(
    db: Session = Depends(get_db),
) -> InstitutionComparisonService:
    return InstitutionComparisonService(_make_graph_service(db))
