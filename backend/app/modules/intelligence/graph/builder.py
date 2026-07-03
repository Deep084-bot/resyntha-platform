"""ResearchGraphBuilder — constructs a ResearchGraph from extracted knowledge.

Single entry point::

    builder = ResearchGraphBuilder()
    graph = builder.build(records, paper_map=paper_map)

Phases (all internal):

1. Normalise record text fields (reuse ``Normalizer``)
2. Resolve canonical entity names (reuse ``EntityResolver``)
3. Build entity indices from resolved names
4. Construct entity nodes from indices
5. Wire object references (PaperNode → *Node)
6. Attach ``GraphServices``
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.modules.analysis.cluster.normalizer import Normalizer
from app.modules.intelligence.graph.models import (
    AuthorNode,
    DatasetNode,
    GraphServices,
    InstitutionNode,
    InstitutionType,
    MethodologyNode,
    MetricNode,
    PaperNode,
    ResearchGraph,
    TechnologyNode,
    TechnologyType,
)
from app.modules.intelligence.graph.resolver import EntityResolver
from app.modules.intelligence.services import (
    CentralityService,
    CoOccurrenceService,
    SimilarityService,
    StatisticsService,
    TrendService,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.modules.extraction.domain.models import ExtractedKnowledge


@dataclass
class PaperMetadata:
    """Lightweight paper metadata extracted from the Paper ORM model.

    Parameters
    ----------
    year:
        Publication year.
    citation_count:
        Number of citations.
    venue:
        Publication venue / conference / journal.
    authors:
        List of author names.
    doi:
        Digital object identifier.
    """

    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    authors: list[str] | None = None
    doi: str | None = None


class ResearchGraphBuilder:
    """Build a ``ResearchGraph`` from ``ExtractedKnowledge`` records.

    Parameters
    ----------
    normalizer:
        Text normalizer.  Defaults to ``Normalizer`` from the
        existing analysis pipeline.
    resolver:
        Entity name resolver.  Defaults to ``EntityResolver``.
    """

    def __init__(
        self,
        normalizer: Normalizer | None = None,
        resolver: EntityResolver | None = None,
    ) -> None:
        self._normalizer = normalizer or Normalizer()
        self._resolver = resolver or EntityResolver()

    # ── Public API ────────────────────────────────────────────────

    def build(
        self,
        records: Sequence[ExtractedKnowledge],
        paper_map: dict[str, PaperMetadata] | None = None,
    ) -> ResearchGraph:
        """Construct a ``ResearchGraph`` from extraction records.

        Parameters
        ----------
        records:
            ``ExtractedKnowledge`` rows for a single investigation.
        paper_map:
            ``{paper_id_str: PaperMetadata}`` — provides year,
            citation count, venue, and author names that are not
            available on ``ExtractedKnowledge`` itself.

        Returns
        -------
        A fully-wired ``ResearchGraph``.
        """
        paper_map = paper_map or {}

        # Phase 1 — normalise all text fields
        normalised = [self._normalise_record(r) for r in records]

        # Phase 2 — build entity indices from resolved names
        indices = self._build_indices(normalised, paper_map)

        # Phase 3 — construct entity + paper nodes
        graph = self._construct_nodes(indices, normalised)

        # Phase 4 — wire object references
        self._wire_references(graph, indices, normalised)

        # Phase 5 — attach services
        self._attach_services(graph)

        return graph

    # ── Phase 1: Normalisation ────────────────────────────────────

    def _normalise_record(self, record: ExtractedKnowledge) -> NormalisedRecord:
        """Normalise and canonicalise every text field in a record.

        For entity names (methodology, institutions, datasets, etc.) the
        resolver is applied **before** the stemmer so that canonical
        aliases (e.g.  ``"RL" → "Reinforcement Learning"``) are matched
        correctly.  For free-text fields (limitations, future work, ...)
        the stemmer is applied for fuzzy grouping.
        """
        resolve_first = self._resolver.resolve
        normalise_text = self._normalizer.normalize
        pid = str(record.paper_id)

        # ── Entity names: resolve to canonical, then stem for storage ──
        methodology_raw = record.methodology or ""
        if methodology_raw.strip():
            canonical = resolve_first(methodology_raw, "methodology")
            methodology = normalise_text(canonical)
        else:
            methodology = ""

        institutions = self._normalise_entity_list(
            getattr(record, "institutions", None) or [], "institution",
        )
        metrics = self._normalise_entity_list(
            getattr(record, "evaluation_metrics", None) or [], "metric",
        )
        datasets = self._normalise_entity_list(
            getattr(record, "datasets_used", None) or [], "dataset",
        )
        technologies = self._normalise_entity_list(
            getattr(record, "technologies", None) or [], "technology",
        )

        # ── Technique names: normalise then resolve ──
        techniques = [
            resolve_first(normalise_text(t), "methodology")
            for t in (record.relevant_techniques or []) if t
        ]

        # ── Free-text fields: full normalisation (stemming) ──
        limitations = [normalise_text(t) for t in (record.limitations or []) if t]
        future_work = [normalise_text(t) for t in (record.future_work or []) if t]
        key_findings = [normalise_text(t) for t in (record.key_findings or []) if t]
        key_contributions = [normalise_text(t) for t in (record.key_contributions or []) if t]
        cited_works = [normalise_text(t) for t in (record.cited_works or []) if t]
        research_domains = [
            resolve_first(normalise_text(t), "methodology")
            for t in (getattr(record, "research_domains", None) or []) if t
        ]

        return NormalisedRecord(
            paper_id=pid,
            title=record.paper_title,
            methodology=methodology,
            techniques=self._dedupe(techniques),
            institutions=self._dedupe(institutions),
            metrics=self._dedupe(metrics),
            datasets=self._dedupe(datasets),
            technologies=self._dedupe(technologies),
            limitations=self._dedupe(limitations),
            future_work=self._dedupe(future_work),
            key_findings=self._dedupe(key_findings),
            key_contributions=self._dedupe(key_contributions),
            cited_works=self._dedupe(cited_works),
            research_domains=self._dedupe(research_domains),
        )

    def _normalise_entity_list(
        self,
        raw: list,
        entity_type: str,
    ) -> list[str]:
        """Normalise a list that may contain strings or dicts.

        Resolves to canonical form first, then applies light stemming
        for consistent dict-key matching.
        """
        resolve_first = self._resolver.resolve
        normalise_text = self._normalizer.normalize
        result: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                name = (
                    item.get("name")
                    or item.get("metric_name")
                    or item.get("dataset_name")
                    or ""
                )
            else:
                name = str(item)
            canonical = resolve_first(name, entity_type)
            cleaned = normalise_text(canonical)
            if cleaned:
                result.append(cleaned)
        return result

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        """Remove duplicates while preserving order."""
        seen: set[str] = set()
        return [x for x in items if not (x in seen or seen.add(x))]

    # ── Phase 2: Index building ───────────────────────────────────

    def _build_indices(
        self,
        normalised: list[NormalisedRecord],
        paper_map: dict[str, PaperMetadata],
    ) -> EntityIndices:
        """Build entity-to-paper ID mappings from normalised records."""
        authors: dict[str, set[str]] = defaultdict(set)
        institutions: dict[str, set[str]] = defaultdict(set)
        methodologies: dict[str, set[str]] = defaultdict(set)
        datasets: dict[str, set[str]] = defaultdict(set)
        technologies: dict[str, set[str]] = defaultdict(set)
        metrics: dict[str, set[str]] = defaultdict(set)
        paper_meta: dict[str, PaperMetadata] = {}
        author_institutions: dict[str, set[str]] = defaultdict(set)
        institution_authors: dict[str, set[str]] = defaultdict(set)

        for rec in normalised:
            pid = rec.paper_id
            if rec.methodology:
                methodologies[rec.methodology].add(pid)
            for tech in rec.techniques:
                methodologies[tech].add(pid)
            for inst in rec.institutions:
                institutions[inst].add(pid)
            for ds in rec.datasets:
                datasets[ds].add(pid)
            for tech in rec.technologies:
                technologies[tech].add(pid)
            for m in rec.metrics:
                metrics[m].add(pid)

            meta = paper_map.get(pid, PaperMetadata())
            paper_meta[pid] = meta

            if meta.authors:
                for author_name in meta.authors:
                    # Authors: resolve only (no stemmer) to preserve display name
                    normalised_name = self._resolver.resolve(author_name, "")
                    if normalised_name:
                        authors[normalised_name].add(pid)
                        for inst in rec.institutions:
                            author_institutions[normalised_name].add(inst)
                            institution_authors[inst].add(normalised_name)

        return EntityIndices(
            authors=dict(authors),
            institutions=dict(institutions),
            methodologies=dict(methodologies),
            datasets=dict(datasets),
            technologies=dict(technologies),
            metrics=dict(metrics),
            paper_meta=paper_meta,
            author_institutions=dict(author_institutions),
            institution_authors=dict(institution_authors),
        )

    # ── Phase 3: Node construction ────────────────────────────────

    def _construct_nodes(
        self,
        indices: EntityIndices,
        normalised: list[NormalisedRecord],
    ) -> ResearchGraph:
        """Create entity + paper nodes from indices."""
        graph = ResearchGraph()

        # Entity nodes
        for name, pids in indices.authors.items():
            first_year = self._earliest_year(pids, indices.paper_meta)
            graph.authors[name] = AuthorNode(
                name=name, paper_ids=sorted(pids),
                first_publication_year=first_year,
            )
        for name, pids in indices.institutions.items():
            graph.institutions[name] = InstitutionNode(
                name=name, type=self._classify_institution(name),
                paper_ids=sorted(pids),
                author_names=sorted(indices.institution_authors.get(name, [])),
            )
        for name, pids in indices.methodologies.items():
            graph.methodologies[name] = MethodologyNode(
                name=name, paper_ids=sorted(pids),
            )
        for name, pids in indices.datasets.items():
            graph.datasets[name] = DatasetNode(name=name, paper_ids=sorted(pids))
        for name, pids in indices.technologies.items():
            graph.technologies[name] = TechnologyNode(
                name=name, type=self._classify_technology(name),
                paper_ids=sorted(pids),
            )
        for name, pids in indices.metrics.items():
            graph.metrics[name] = MetricNode(name=name, paper_ids=sorted(pids))

        # Paper nodes
        normalised_by_id = {rec.paper_id: rec for rec in normalised}
        for pid, meta in indices.paper_meta.items():
            rec = normalised_by_id.get(pid)
            graph.papers[pid] = PaperNode(
                id=pid,
                title=rec.title if rec else "",
                year=meta.year,
                citation_count=meta.citation_count,
                venue=meta.venue,
                techniques=rec.techniques if rec else [],
                limitations=rec.limitations if rec else [],
                future_work=rec.future_work if rec else [],
                key_findings=rec.key_findings if rec else [],
                key_contributions=rec.key_contributions if rec else [],
                cited_works=rec.cited_works if rec else [],
                research_domains=rec.research_domains if rec else [],
            )

        return graph

    # ── Phase 4: Reference wiring ─────────────────────────────────

    def _wire_references(
        self,
        graph: ResearchGraph,
        indices: EntityIndices,
        normalised: list[NormalisedRecord],
    ) -> None:
        """Wire object references between entity nodes."""
        normalised_by_id = {rec.paper_id: rec for rec in normalised}

        for pid, paper in graph.papers.items():
            meta = indices.paper_meta.get(pid)
            rec = normalised_by_id.get(pid)

            # Authors
            if meta and meta.authors:
                for author_name in meta.authors:
                    norm = self._resolver.resolve(author_name, "")
                    if norm in graph.authors:
                        paper.authors.append(graph.authors[norm])

            if rec is None:
                continue

            # Institutions
            for name in rec.institutions:
                if name in graph.institutions:
                    paper.institutions.append(graph.institutions[name])

            # Methodologies (methodology scalar + techniques list)
            method_names: list[str] = []
            if rec.methodology:
                method_names.append(rec.methodology)
            method_names.extend(rec.techniques)
            for name in method_names:
                if name in graph.methodologies:
                    paper.methodologies.append(graph.methodologies[name])

            # Datasets
            for name in rec.datasets:
                if name in graph.datasets:
                    paper.datasets.append(graph.datasets[name])

            # Technologies
            for name in rec.technologies:
                if name in graph.technologies:
                    paper.technologies.append(graph.technologies[name])

            # Metrics
            for name in rec.metrics:
                if name in graph.metrics:
                    paper.metrics.append(graph.metrics[name])

        # Author ↔ Institution wiring
        for author_name, inst_names in indices.author_institutions.items():
            author = graph.authors.get(author_name)
            if author:
                for inst_name in inst_names:
                    inst = graph.institutions.get(inst_name)
                    if inst:
                        author.affiliated_institutions.append(inst)

    # ── Phase 5: Services ─────────────────────────────────────────

    @staticmethod
    def _attach_services(graph: ResearchGraph) -> None:
        graph.services = GraphServices(
            co_occurrence=CoOccurrenceService(graph),
            trends=TrendService(graph),
            similarity=SimilarityService(graph),
            centrality=CentralityService(graph),
            statistics=StatisticsService(graph),
        )

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _earliest_year(
        paper_ids: set[str],
        paper_meta: dict[str, PaperMetadata],
    ) -> int | None:
        years = [
            paper_meta[pid].year for pid in paper_ids
            if pid in paper_meta and paper_meta[pid].year is not None
        ]
        return min(years) if years else None

    @staticmethod
    def _classify_institution(name: str) -> InstitutionType:
        lower = name.lower()
        if any(t in lower for t in ("university", "college", "institute of technology",
                                     "eth", "mit", "caltech")):
            return InstitutionType.UNIVERSITY
        if any(t in lower for t in ("lab", "laboratory", "research center", "research centre")):
            return InstitutionType.LAB
        if any(t in lower for t in ("google", "microsoft", "meta", "amazon", "apple",
                                     "nvidia", "ibm", "openai", "inc", "corp", "ltd",
                                     "anthropic", "deepmind")):
            return InstitutionType.COMPANY
        if any(t in lower for t in ("government", "national", "department of", "ministry",
                                     "agency")):
            return InstitutionType.GOVERNMENT
        return InstitutionType.OTHER

    @staticmethod
    def _classify_technology(name: str) -> TechnologyType:
        lower = name.lower()
        if any(t in lower for t in ("pytorch", "tensorflow", "jax", "keras", "django",
                                     "flask", "react", "angular", "spring")):
            return TechnologyType.FRAMEWORK
        if any(t in lower for t in ("lib", "library", "numpy", "scipy", "sklearn",
                                     "opencv", "pandas")):
            return TechnologyType.LIBRARY
        if any(t in lower for t in ("cuda", "docker", "kubernetes", "git", "nginx",
                                     "redis")):
            return TechnologyType.TOOL
        return TechnologyType.OTHER


# ── Internal helpers ───────────────────────────────────────────────


@dataclass
class NormalisedRecord:
    """Intermediate representation after normalisation."""

    paper_id: str = ""
    title: str = ""
    methodology: str = ""
    techniques: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    future_work: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    key_contributions: list[str] = field(default_factory=list)
    cited_works: list[str] = field(default_factory=list)
    research_domains: list[str] = field(default_factory=list)


@dataclass
class EntityIndices:
    """Entity → paper ID mappings (pre-node-construction)."""

    authors: dict[str, set[str]] = field(default_factory=dict)
    institutions: dict[str, set[str]] = field(default_factory=dict)
    methodologies: dict[str, set[str]] = field(default_factory=dict)
    datasets: dict[str, set[str]] = field(default_factory=dict)
    technologies: dict[str, set[str]] = field(default_factory=dict)
    metrics: dict[str, set[str]] = field(default_factory=dict)
    paper_meta: dict[str, PaperMetadata] = field(default_factory=dict)
    author_institutions: dict[str, set[str]] = field(default_factory=dict)
    institution_authors: dict[str, set[str]] = field(default_factory=dict)
