"""Pydantic response schemas for the Intelligence REST API.

These models mirror the JSON renderer output stored in the artifact
payload so that existing pipeline artifacts deserialise without
transformation.
"""

from __future__ import annotations

from pydantic import BaseModel

# ── Entry types ────────────────────────────────────────────────────


class InstitutionEntryResponse(BaseModel):
    name: str
    type: str
    paper_count: int
    author_count: int


class MethodologyEntryResponse(BaseModel):
    name: str
    paper_count: int
    technique_count: int = 0
    techniques: list[str] = []


class TopEntityResponse(BaseModel):
    name: str
    paper_count: int


class CentralityEntryResponse(BaseModel):
    name: str
    centrality: float


class CollaborationPairResponse(BaseModel):
    source: str
    target: str
    weight: int


class ObservationResponse(BaseModel):
    category: str
    label: str
    value: str


# ── Section models ──────────────────────────────────────────────


class OverviewSectionResponse(BaseModel):
    total_papers: int = 0
    years_covered: list[int] = []
    total_institutions: int = 0
    total_methodologies: int = 0
    total_technologies: int = 0
    total_datasets: int = 0
    total_authors: int = 0


class InstitutionSectionResponse(BaseModel):
    total: int = 0
    type_distribution: dict[str, int] = {}
    top_institutions: list[InstitutionEntryResponse] = []


class MethodologySectionResponse(BaseModel):
    total: int = 0
    methodologies: list[MethodologyEntryResponse] = []


class TechnologyDiversityResponse(BaseModel):
    total_technologies: int = 0
    papers_with_technology: int = 0
    avg_papers_per_technology: float = 0.0


class TechnologySectionResponse(BaseModel):
    total: int = 0
    top_technologies: list[TopEntityResponse] = []
    first_appearance_by_year: dict[str, int] = {}
    diversity: TechnologyDiversityResponse | None = None


class DatasetDiversityResponse(BaseModel):
    total_datasets: int = 0
    papers_with_dataset: int = 0
    avg_papers_per_dataset: float = 0.0


class DatasetSectionResponse(BaseModel):
    total: int = 0
    top_datasets: list[TopEntityResponse] = []
    diversity: DatasetDiversityResponse | None = None


class TemporalSectionResponse(BaseModel):
    years_covered: list[int] = []
    total_papers: int = 0
    papers_per_year: dict[int, int] = {}


class NetworkResponse(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    degree_centrality: dict[str, float] = {}
    top_by_centrality: list[CentralityEntryResponse] = []


class CollaborationSectionResponse(BaseModel):
    institution_network: NetworkResponse | None = None
    institution_collaborations: list[CollaborationPairResponse] | None = None
    author_network: NetworkResponse | None = None
    author_collaborations: list[CollaborationPairResponse] | None = None


# ── Top-level response ─────────────────────────────────────────


class LandscapeResponse(BaseModel):
    """Full landscape response deserialised from the JSON artifact payload."""

    overview: OverviewSectionResponse | None = None
    institutions: InstitutionSectionResponse | None = None
    methodologies: MethodologySectionResponse | None = None
    technologies: TechnologySectionResponse | None = None
    datasets: DatasetSectionResponse | None = None
    temporal: TemporalSectionResponse | None = None
    collaborations: CollaborationSectionResponse | None = None
    observations: list[ObservationResponse] | None = None


class MarkdownResponse(BaseModel):
    """Envelope for raw markdown content."""

    markdown: str
