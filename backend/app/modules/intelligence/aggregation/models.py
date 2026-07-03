from __future__ import annotations

from dataclasses import dataclass, field

# ── Entry types (typed replacements for dict[str, Any]) ─────────────


@dataclass
class InstitutionEntry:
    name: str
    type: str
    paper_count: int
    author_count: int


@dataclass
class MethodologyEntry:
    name: str
    paper_count: int
    technique_count: int
    techniques: list[str] = field(default_factory=list)


@dataclass
class DiversityMetrics:
    total: int = 0
    papers_with_entity: int = 0
    avg_papers_per_entity: float = 0.0


@dataclass
class NetworkSection:
    total_nodes: int = 0
    total_edges: int = 0
    degree_centrality: dict[str, float] = field(default_factory=dict)
    top_by_centrality: list[tuple[str, float]] = field(default_factory=list)


# ── Section models ─────────────────────────────────────────────────


@dataclass
class OverviewSection:
    total_papers: int = 0
    years_covered: list[int] = field(default_factory=list)
    total_institutions: int = 0
    total_methodologies: int = 0
    total_technologies: int = 0
    total_datasets: int = 0
    total_authors: int = 0


@dataclass
class InstitutionSection:
    total: int = 0
    type_distribution: dict[str, int] = field(default_factory=dict)
    top_institutions: list[InstitutionEntry] = field(default_factory=list)
    institutions_by_type: dict[str, list[InstitutionEntry]] = field(
        default_factory=dict,
    )


@dataclass
class MethodologySection:
    total: int = 0
    top_methodologies: list[MethodologyEntry] = field(default_factory=list)


@dataclass
class TechnologySection:
    total: int = 0
    top_technologies: list[tuple[str, int]] = field(default_factory=list)
    first_appearance_by_year: dict[str, int | None] = field(default_factory=dict)
    diversity: DiversityMetrics = field(default_factory=DiversityMetrics)


@dataclass
class DatasetSection:
    total: int = 0
    top_datasets: list[tuple[str, int]] = field(default_factory=list)
    yearly_usage_trends: dict[str, dict[int, int]] = field(default_factory=dict)
    diversity: DiversityMetrics = field(default_factory=DiversityMetrics)


@dataclass
class TemporalSection:
    years_covered: list[int] = field(default_factory=list)
    papers_per_year: dict[int, int] = field(default_factory=dict)
    total_papers: int = 0


@dataclass
class CollaborationSection:
    institution_network: NetworkSection = field(default_factory=NetworkSection)
    author_network: NetworkSection = field(default_factory=NetworkSection)
    top_institution_collaborations: list[tuple[str, str, int]] = field(
        default_factory=list,
    )
    top_author_collaborations: list[tuple[str, str, int]] = field(
        default_factory=list,
    )


@dataclass
class StatisticsSection:
    papers_per_year: dict[int, int] = field(default_factory=dict)
    total_papers: int = 0


@dataclass
class Observation:
    category: str
    label: str
    value: str


# ── Root result ────────────────────────────────────────────────────


@dataclass
class LandscapeResult:
    overview: OverviewSection = field(default_factory=OverviewSection)
    institutions: InstitutionSection = field(default_factory=InstitutionSection)
    methodologies: MethodologySection = field(default_factory=MethodologySection)
    technologies: TechnologySection = field(default_factory=TechnologySection)
    datasets: DatasetSection = field(default_factory=DatasetSection)
    temporal: TemporalSection = field(default_factory=TemporalSection)
    collaborations: CollaborationSection = field(default_factory=CollaborationSection)
    statistics: StatisticsSection = field(default_factory=StatisticsSection)
    observations: list[Observation] = field(default_factory=list)
