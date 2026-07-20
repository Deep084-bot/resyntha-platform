"""Institution Intelligence REST API — search, ranking, trends, comparison.

All endpoints under ``/investigations/{investigation_id}/institutions``.
Existing ``/institution-profiles`` endpoints are NOT modified.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.cache import cached
from app.modules.institution.api.dependencies import (
    get_institution_analytics_service,
    get_institution_comparison_service,
    get_institution_search_service,
)
from app.modules.institution.api.schemas import (
    AuthorEntryResponse,
    CollaborationEntryResponse,
    CompareV2Request,
    EntityCountResponse,
    FilterRequest,
    InstitutionComparisonDetailResponse,
    InstitutionIntelligenceResponse,
    InstitutionRankingEntryResponse,
    InstitutionSearchResultResponse,
    InstitutionTrendResponse,
    PaperEntryResponse,
    TopicSearchResultResponse,
    YearlyTrendResponse,
)
from app.modules.institution.domain.models import (
    InstitutionComparisonDetail,
    InstitutionIntelligence,
    InstitutionRankingEntry,
    InstitutionTrend,
    TopicSearchResult,
)
from app.modules.institution.service.comparison import (
    InstitutionComparisonService,
)
from app.modules.institution.service.ranking import (
    InstitutionAnalyticsService,
)
from app.modules.institution.service.search import (
    InstitutionSearchService,
)
from app.observability.logger import get_logger

router = APIRouter(
    prefix="/investigations/{investigation_id}/institutions",
    tags=["institution-intelligence"],
)
logger = get_logger(__name__)


# ── Search ─────────────────────────────────────────────────────────


@router.get("/search")
@cached("institution_search:{investigation_id}:{q}:{limit}", ttl=1800)
async def search_institutions(
    investigation_id: uuid.UUID,
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    svc: InstitutionSearchService = Depends(get_institution_search_service),
) -> list[InstitutionSearchResultResponse]:
    """Search institutions by name (partial, fuzzy, ranked)."""
    results = svc.search(investigation_id, q, limit=limit)
    return [
        InstitutionSearchResultResponse(
            name=r.name,
            type=r.type,
            paper_count=r.paper_count,
            author_count=r.author_count,
            citation_count=r.citation_count,
            relevance_score=r.relevance_score,
        )
        for r in results
    ]


@router.get("/topic")
@cached("institution_topic:{investigation_id}:{q}:{limit}", ttl=1800)
async def topic_search(
    investigation_id: uuid.UUID,
    q: str = Query(..., description="Research topic query"),
    limit: int = Query(10, ge=1, le=100),
    svc: InstitutionSearchService = Depends(get_institution_search_service),
) -> list[TopicSearchResultResponse]:
    """Search institutions by research topic (domain, technology, dataset, methodology)."""
    results = svc.topic_search(investigation_id, q, limit=limit)
    return [_topic_to_response(r) for r in results]


@router.post("/filter")
@cached("institution_filter:{investigation_id}:{body}", ttl=1800)
async def filter_institutions(
    investigation_id: uuid.UUID,
    body: FilterRequest,
    svc: InstitutionSearchService = Depends(get_institution_search_service),
) -> list[InstitutionSearchResultResponse]:
    """Filter institutions by research criteria."""
    results = svc.filter_institutions(
        investigation_id,
        research_domains=body.research_domains or None,
        technologies=body.technologies or None,
        datasets=body.datasets or None,
        methodologies=body.methodologies or None,
        min_year=body.min_year,
        max_year=body.max_year,
        min_citations=body.min_citations,
        min_papers=body.min_papers,
        limit=body.limit,
    )
    return [
        InstitutionSearchResultResponse(
            name=r.name,
            type=r.type,
            paper_count=r.paper_count,
            author_count=r.author_count,
            citation_count=r.citation_count,
            relevance_score=r.relevance_score,
        )
        for r in results
    ]


# ── Ranking ────────────────────────────────────────────────────────


@router.get("/ranking")
@cached("institution_ranking:{investigation_id}:{by}:{limit}", ttl=1800)
async def rank_institutions(
    investigation_id: uuid.UUID,
    by: str = Query("publication_count", description="Ranking criterion"),
    limit: int = Query(10, ge=1, le=100),
    svc: InstitutionAnalyticsService = Depends(get_institution_analytics_service),
) -> list[InstitutionRankingEntryResponse]:
    """Rank institutions by a given metric."""
    results = svc.rank(investigation_id, criterion=by, limit=limit)
    return [_ranking_to_response(r) for r in results]


# ── Intelligence ───────────────────────────────────────────────────


@router.get("/intelligence")
@cached("institution_intelligence:{investigation_id}", ttl=1800)
async def institution_intelligence(
    investigation_id: uuid.UUID,
    svc: InstitutionAnalyticsService = Depends(get_institution_analytics_service),
) -> InstitutionIntelligenceResponse:
    """Generate intelligence report: top, emerging, collaborative, fastest-growing, leaders."""
    result = svc.get_intelligence(investigation_id)
    return _intelligence_to_response(result)


# ── Trends ─────────────────────────────────────────────────────────


@router.get("/trends")
@cached("institution_trends:{investigation_id}:{names}", ttl=1800)
async def institution_trends(
    investigation_id: uuid.UUID,
    names: str = Query("", description="Comma-separated institution names"),
    svc: InstitutionAnalyticsService = Depends(get_institution_analytics_service),
) -> list[InstitutionTrendResponse]:
    """Get publication growth, technology adoption, and research evolution trends."""
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    results = (
        svc.get_trends(investigation_id, name_list)
        if name_list
        else svc.get_all_trends(investigation_id)
    )
    return [_trend_to_response(r) for r in results]


# ── Comparison 2.0 ────────────────────────────────────────────────


@router.post("/compare-v2")
async def compare_institutions_v2(
    investigation_id: uuid.UUID,
    body: CompareV2Request,
    svc: InstitutionComparisonService = Depends(get_institution_comparison_service),
) -> list[InstitutionComparisonDetailResponse]:
    """Extended comparison with strengths, weaknesses, specializations, and overlap."""
    results = svc.compare(investigation_id, body.institution_names)
    return [_comparison_to_response(r) for r in results]


# ── Response converters ────────────────────────────────────────────


def _topic_to_response(r: TopicSearchResult) -> TopicSearchResultResponse:
    return TopicSearchResultResponse(
        institution_name=r.institution_name,
        paper_count=r.paper_count,
        citation_count=r.citation_count,
        top_papers=[
            PaperEntryResponse(
                id=p.id,
                title=p.title,
                year=p.year,
                citation_count=p.citation_count,
                venue=p.venue,
                authors=p.authors,
                research_domains=p.research_domains,
            )
            for p in r.top_papers
        ],
        top_authors=[
            AuthorEntryResponse(name=a.name, paper_count=a.paper_count) for a in r.top_authors
        ],
        relevance_score=r.relevance_score,
    )


def _ranking_to_response(r: InstitutionRankingEntry) -> InstitutionRankingEntryResponse:
    return InstitutionRankingEntryResponse(
        name=r.name,
        type=r.type,
        paper_count=r.paper_count,
        citation_count=r.citation_count,
        avg_citations=r.avg_citations,
        growth_rate=r.growth_rate,
        technology_diversity=r.technology_diversity,
        research_diversity=r.research_diversity,
        collaboration_score=r.collaboration_score,
        rank=r.rank,
    )


def _intelligence_to_response(r: InstitutionIntelligence) -> InstitutionIntelligenceResponse:
    return InstitutionIntelligenceResponse(
        top_institutions=[_ranking_to_response(e) for e in r.top_institutions],
        emerging_institutions=[_ranking_to_response(e) for e in r.emerging_institutions],
        most_collaborative=[_ranking_to_response(e) for e in r.most_collaborative],
        fastest_growing=[_ranking_to_response(e) for e in r.fastest_growing],
        technology_leaders=[_ranking_to_response(e) for e in r.technology_leaders],
        dataset_leaders=[_ranking_to_response(e) for e in r.dataset_leaders],
        methodology_leaders=[_ranking_to_response(e) for e in r.methodology_leaders],
    )


def _trend_to_response(r: InstitutionTrend) -> InstitutionTrendResponse:
    return InstitutionTrendResponse(
        name=r.name,
        yearly_publications=[
            YearlyTrendResponse(year=yt.year, paper_count=yt.paper_count)
            for yt in r.yearly_publications
        ],
        growth_rate=r.growth_rate,
        is_emerging=r.is_emerging,
        technology_adoption=[
            EntityCountResponse(name=t.name, count=t.count) for t in r.technology_adoption
        ],
        research_evolution=[
            EntityCountResponse(name=rd.name, count=rd.count) for rd in r.research_evolution
        ],
    )


def _comparison_to_response(r: InstitutionComparisonDetail) -> InstitutionComparisonDetailResponse:
    return InstitutionComparisonDetailResponse(
        name=r.name,
        type=r.type,
        total_papers=r.total_papers,
        total_citations=r.total_citations,
        total_authors=r.total_authors,
        avg_citations=r.avg_citations,
        growth_rate=r.growth_rate,
        research_diversity_score=r.research_diversity_score,
        collaboration_score=r.collaboration_score,
        strengths=r.strengths,
        weaknesses=r.weaknesses,
        specializations=[
            EntityCountResponse(name=s.name, count=s.count) for s in r.specializations
        ],
        top_papers=[
            PaperEntryResponse(
                id=p.id,
                title=p.title,
                year=p.year,
                citation_count=p.citation_count,
                venue=p.venue,
                authors=p.authors,
                research_domains=p.research_domains,
            )
            for p in r.top_papers
        ],
        yearly_trends=[
            YearlyTrendResponse(year=yt.year, paper_count=yt.paper_count) for yt in r.yearly_trends
        ],
        collaborating_institutions=[
            CollaborationEntryResponse(
                institution_name=ci.institution_name,
                joint_paper_count=ci.joint_paper_count,
            )
            for ci in r.collaborating_institutions
        ],
    )
