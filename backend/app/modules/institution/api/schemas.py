from __future__ import annotations

from pydantic import BaseModel


class EntityCountResponse(BaseModel):
    name: str
    count: int


class AuthorEntryResponse(BaseModel):
    name: str
    paper_count: int
    affiliated_institutions: list[str] = []


class PaperEntryResponse(BaseModel):
    id: str
    title: str
    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    authors: list[str] = []
    research_domains: list[str] = []


class CollaborationEntryResponse(BaseModel):
    institution_name: str
    joint_paper_count: int


class YearlyTrendResponse(BaseModel):
    year: int
    paper_count: int


class InstitutionProfileResponse(BaseModel):
    name: str
    type: str
    total_papers: int
    total_authors: int
    total_citations: int
    research_domains: list[EntityCountResponse] = []
    technologies: list[EntityCountResponse] = []
    datasets: list[EntityCountResponse] = []
    methodologies: list[EntityCountResponse] = []
    top_authors: list[AuthorEntryResponse] = []
    top_papers: list[PaperEntryResponse] = []
    yearly_trends: list[YearlyTrendResponse] = []
    collaborating_institutions: list[CollaborationEntryResponse] = []
    co_authors: list[AuthorEntryResponse] = []


class CompareRequest(BaseModel):
    institution_names: list[str]


# ── Search schemas ─────────────────────────────────────────────────


class InstitutionSearchResultResponse(BaseModel):
    name: str
    type: str
    paper_count: int
    author_count: int
    citation_count: int
    relevance_score: float


class TopicSearchResultResponse(BaseModel):
    institution_name: str
    paper_count: int
    citation_count: int
    top_papers: list[PaperEntryResponse] = []
    top_authors: list[AuthorEntryResponse] = []
    relevance_score: float = 0.0


class FilterRequest(BaseModel):
    research_domains: list[str] = []
    technologies: list[str] = []
    datasets: list[str] = []
    methodologies: list[str] = []
    min_year: int | None = None
    max_year: int | None = None
    min_citations: int | None = None
    min_papers: int | None = None
    limit: int = 50


# ── Ranking schemas ────────────────────────────────────────────────


class InstitutionRankingEntryResponse(BaseModel):
    name: str
    type: str
    paper_count: int
    citation_count: int
    avg_citations: float
    growth_rate: float
    technology_diversity: int
    research_diversity: int
    collaboration_score: float
    rank: int


class InstitutionIntelligenceResponse(BaseModel):
    top_institutions: list[InstitutionRankingEntryResponse] = []
    emerging_institutions: list[InstitutionRankingEntryResponse] = []
    most_collaborative: list[InstitutionRankingEntryResponse] = []
    fastest_growing: list[InstitutionRankingEntryResponse] = []
    technology_leaders: list[InstitutionRankingEntryResponse] = []
    dataset_leaders: list[InstitutionRankingEntryResponse] = []
    methodology_leaders: list[InstitutionRankingEntryResponse] = []


class InstitutionTrendResponse(BaseModel):
    name: str
    yearly_publications: list[YearlyTrendResponse] = []
    growth_rate: float = 0.0
    is_emerging: bool = False
    technology_adoption: list[EntityCountResponse] = []
    research_evolution: list[EntityCountResponse] = []


class TrendQueryParams(BaseModel):
    names: str = ""


class RankQueryParams(BaseModel):
    by: str = "publication_count"
    limit: int = 10


# ── Comparison 2.0 schemas ─────────────────────────────────────────


class InstitutionComparisonDetailResponse(BaseModel):
    name: str
    type: str
    total_papers: int
    total_citations: int
    total_authors: int
    avg_citations: float
    growth_rate: float
    research_diversity_score: float
    collaboration_score: float
    strengths: list[str] = []
    weaknesses: list[str] = []
    specializations: list[EntityCountResponse] = []
    top_papers: list[PaperEntryResponse] = []
    yearly_trends: list[YearlyTrendResponse] = []
    collaborating_institutions: list[CollaborationEntryResponse] = []


class CompareV2Request(BaseModel):
    institution_names: list[str]
