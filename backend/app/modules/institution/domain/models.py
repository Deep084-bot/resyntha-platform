from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EntityCount:
    name: str
    count: int


@dataclass
class AuthorEntry:
    name: str
    paper_count: int
    affiliated_institutions: list[str] = field(default_factory=list)


@dataclass
class PaperEntry:
    id: str
    title: str
    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    authors: list[str] = field(default_factory=list)
    research_domains: list[str] = field(default_factory=list)


@dataclass
class CollaborationEntry:
    institution_name: str
    joint_paper_count: int


@dataclass
class YearlyTrend:
    year: int
    paper_count: int


@dataclass
class InstitutionProfile:
    name: str
    type: str
    total_papers: int
    total_authors: int
    total_citations: int
    research_domains: list[EntityCount] = field(default_factory=list)
    technologies: list[EntityCount] = field(default_factory=list)
    datasets: list[EntityCount] = field(default_factory=list)
    methodologies: list[EntityCount] = field(default_factory=list)
    top_authors: list[AuthorEntry] = field(default_factory=list)
    top_papers: list[PaperEntry] = field(default_factory=list)
    yearly_trends: list[YearlyTrend] = field(default_factory=list)
    collaborating_institutions: list[CollaborationEntry] = field(default_factory=list)
    co_authors: list[AuthorEntry] = field(default_factory=list)


# ── Search models ──────────────────────────────────────────────────


@dataclass
class InstitutionSearchResult:
    name: str
    type: str
    paper_count: int
    author_count: int
    citation_count: int
    relevance_score: float


@dataclass
class TopicSearchResult:
    institution_name: str
    paper_count: int
    citation_count: int
    top_papers: list[PaperEntry] = field(default_factory=list)
    top_authors: list[AuthorEntry] = field(default_factory=list)
    relevance_score: float = 0.0


# ── Ranking models ─────────────────────────────────────────────────


@dataclass
class InstitutionRankingEntry:
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


@dataclass
class InstitutionIntelligence:
    top_institutions: list[InstitutionRankingEntry] = field(default_factory=list)
    emerging_institutions: list[InstitutionRankingEntry] = field(default_factory=list)
    most_collaborative: list[InstitutionRankingEntry] = field(default_factory=list)
    fastest_growing: list[InstitutionRankingEntry] = field(default_factory=list)
    technology_leaders: list[InstitutionRankingEntry] = field(default_factory=list)
    dataset_leaders: list[InstitutionRankingEntry] = field(default_factory=list)
    methodology_leaders: list[InstitutionRankingEntry] = field(default_factory=list)


@dataclass
class InstitutionTrend:
    name: str
    yearly_publications: list[YearlyTrend] = field(default_factory=list)
    growth_rate: float = 0.0
    is_emerging: bool = False
    technology_adoption: list[EntityCount] = field(default_factory=list)
    research_evolution: list[EntityCount] = field(default_factory=list)


# ── Comparison 2.0 models ──────────────────────────────────────────


@dataclass
class InstitutionComparisonDetail:
    name: str
    type: str
    total_papers: int
    total_citations: int
    total_authors: int
    avg_citations: float
    growth_rate: float
    research_diversity_score: float
    collaboration_score: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    specializations: list[EntityCount] = field(default_factory=list)
    top_papers: list[PaperEntry] = field(default_factory=list)
    yearly_trends: list[YearlyTrend] = field(default_factory=list)
    collaborating_institutions: list[CollaborationEntry] = field(default_factory=list)
