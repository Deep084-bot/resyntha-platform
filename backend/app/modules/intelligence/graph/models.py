"""ResearchGraph entity models.

Every node is a ``dataclass``.  Entity-to-entity references use
object pointers in the forward direction (PaperNode → AuthorNode)
and string IDs for back-references (AuthorNode → paper_ids) to
keep serialisation simple and avoid cycles.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ── Enums ──────────────────────────────────────────────────────────


class InstitutionType(enum.StrEnum):
    UNIVERSITY = "university"
    COMPANY = "company"
    LAB = "lab"
    GOVERNMENT = "government"
    OTHER = "other"


class TechnologyType(enum.StrEnum):
    FRAMEWORK = "framework"
    LIBRARY = "library"
    TOOL = "tool"
    PLATFORM = "platform"
    OTHER = "other"


# ── Entity nodes ───────────────────────────────────────────────────


@dataclass
class PaperNode:
    """A single paper in the investigation corpus."""

    id: str
    title: str
    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    authors: list[AuthorNode] = field(default_factory=list)
    institutions: list[InstitutionNode] = field(default_factory=list)
    methodologies: list[MethodologyNode] = field(default_factory=list)
    datasets: list[DatasetNode] = field(default_factory=list)
    technologies: list[TechnologyNode] = field(default_factory=list)
    metrics: list[MetricNode] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    future_work: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    key_contributions: list[str] = field(default_factory=list)
    cited_works: list[str] = field(default_factory=list)
    research_domains: list[str] = field(default_factory=list)


@dataclass
class AuthorNode:
    """A researcher / author."""

    name: str
    paper_ids: list[str] = field(default_factory=list)
    affiliated_institutions: list[InstitutionNode] = field(default_factory=list)
    first_publication_year: int | None = None


@dataclass
class InstitutionNode:
    """A university, company, lab, or other institution."""

    name: str
    type: InstitutionType = InstitutionType.OTHER
    country: str | None = None
    paper_ids: list[str] = field(default_factory=list)
    author_names: list[str] = field(default_factory=list)


@dataclass
class MethodologyNode:
    """A research methodology or approach."""

    name: str
    paper_ids: list[str] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)


@dataclass
class DatasetNode:
    """A named dataset used in one or more papers."""

    name: str
    paper_ids: list[str] = field(default_factory=list)


@dataclass
class TechnologyNode:
    """A framework, library, tool, or platform."""

    name: str
    type: TechnologyType = TechnologyType.OTHER
    paper_ids: list[str] = field(default_factory=list)


@dataclass
class MetricNode:
    """An evaluation metric."""

    name: str
    paper_ids: list[str] = field(default_factory=list)


# ── Graph services container (forward reference) ───────────────────


@dataclass
class GraphServices:
    """Container for algorithm services attached to the graph.

    Every service is a stub in Sprint 2.2; implementations will be
    added in later sprints alongside the first analyzers.
    """

    co_occurrence: object = field(default=None)
    trends: object = field(default=None)
    similarity: object = field(default=None)
    centrality: object = field(default=None)
    statistics: object = field(default=None)


# ── Root graph object ──────────────────────────────────────────────


@dataclass
class ResearchGraph:
    """In-memory entity graph for a single investigation.

    Built once per execution by ``ResearchGraphBuilder`` and consumed
    by every intelligence analyzer.  Ephemeral — never persisted
    directly (artifacts carry the structured output instead).
    """

    papers: dict[str, PaperNode] = field(default_factory=dict)
    authors: dict[str, AuthorNode] = field(default_factory=dict)
    institutions: dict[str, InstitutionNode] = field(default_factory=dict)
    methodologies: dict[str, MethodologyNode] = field(default_factory=dict)
    datasets: dict[str, DatasetNode] = field(default_factory=dict)
    technologies: dict[str, TechnologyNode] = field(default_factory=dict)
    metrics: dict[str, MetricNode] = field(default_factory=dict)
    services: GraphServices = field(default_factory=GraphServices)

    @property
    def paper_count(self) -> int:
        return len(self.papers)

    @property
    def years(self) -> list[int]:
        """Sorted list of distinct publication years across papers."""
        result: set[int] = set()
        for p in self.papers.values():
            if p.year is not None:
                result.add(p.year)
        return sorted(result)

    def year_index(self, year: int) -> list[PaperNode]:
        """Return papers published in *year*."""
        return [p for p in self.papers.values() if p.year == year]
