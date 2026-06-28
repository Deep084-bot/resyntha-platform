"""ResearchLandscape domain model.

Produced by the analysis engine from all ``ExtractedKnowledge``
records belonging to an investigation.
"""

from pydantic import BaseModel, Field


class RankedItem(BaseModel):
    """A named item with its frequency and relative percentage."""

    name: str
    count: int
    percentage: float


class CitationStats(BaseModel):
    """Citation statistics across all papers."""

    total: int = 0
    average: float = 0.0
    median: float = 0.0
    max: int = 0
    min: int = 0
    total_with_data: int = 0


class PublicationYearDistribution(BaseModel):
    """Paper count grouped by publication year."""

    years: dict[str, int] = Field(default_factory=dict)


class VenueDistribution(BaseModel):
    """Paper count grouped by venue name."""

    venues: dict[str, int] = Field(default_factory=dict)


class ResearchLandscape(BaseModel):
    """Aggregated cross-paper analysis for an investigation."""

    paper_count: int = 0
    methodologies: list[RankedItem] = Field(default_factory=list)
    datasets: list[RankedItem] = Field(default_factory=list)
    evaluation_metrics: list[RankedItem] = Field(default_factory=list)
    research_domains: list[RankedItem] = Field(default_factory=list)
    tasks: list[RankedItem] = Field(default_factory=list)
    applications: list[RankedItem] = Field(default_factory=list)
    limitations: list[RankedItem] = Field(default_factory=list)
    future_work: list[RankedItem] = Field(default_factory=list)
    keywords: list[RankedItem] = Field(default_factory=list)
    novel_contributions: list[RankedItem] = Field(default_factory=list)
    top_authors: list[RankedItem] = Field(default_factory=list)
    publication_year_distribution: PublicationYearDistribution = Field(
        default_factory=PublicationYearDistribution,
    )
    venue_distribution: VenueDistribution = Field(
        default_factory=VenueDistribution,
    )
    citation_statistics: CitationStats = Field(
        default_factory=CitationStats,
    )
    clusters: dict[str, list[RankedItem]] = Field(default_factory=dict)
    generated_at: str = ""
