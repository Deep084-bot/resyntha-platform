"""Unit tests for the Research Intelligence Engine infrastructure.

Covers:
  - EntityResolver (canonicalisation, aliases)
  - ResearchGraph domain models (properties, year index)
  - ResearchGraphBuilder (construction, references, services)
  - AnalysisContext (construction)
  - IntelligenceConfig (defaults)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.modules.intelligence import (
    AnalysisContext,
    AuthorNode,
    CentralityService,
    CoOccurrenceService,
    DatasetNode,
    EntityResolver,
    InstitutionNode,
    InstitutionType,
    IntelligenceConfig,
    MethodologyNode,
    MetricNode,
    PaperMetadata,
    PaperNode,
    ResearchGraph,
    ResearchGraphBuilder,
    SimilarityService,
    StatisticsService,
    TechnologyNode,
    TechnologyType,
    TrendService,
)

# ── Deterministic test UUIDs ───────────────────────────────────────
P1_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
P2_UUID = uuid.UUID("00000000-0000-0000-0000-000000000002")
P3_UUID = uuid.UUID("00000000-0000-0000-0000-000000000003")
P1_STR = str(P1_UUID)
P2_STR = str(P2_UUID)
P3_STR = str(P3_UUID)


# ======================================================================
# EntityResolver
# ======================================================================


class TestEntityResolver:
    def test_passthrough_for_unknown_name(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("Some Random Lab", "institution") == "Some Random Lab"

    def test_canonicalises_known_alias(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("mit", "institution") == "Massachusetts Institute of Technology"
        assert resolver.resolve("MIT", "institution") == "Massachusetts Institute of Technology"

    def test_case_insensitive_resolution(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("GOOGLE", "institution") == "Google"
        assert resolver.resolve("google", "institution") == "Google"

    def test_whitespace_stripping(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("  MIT  ", "institution") == "Massachusetts Institute of Technology"

    def test_add_alias_dynamically(self) -> None:
        resolver = EntityResolver()
        resolver.add_alias("my lab", "My Research Lab", "institution")
        assert resolver.resolve("My Lab", "institution") == "My Research Lab"

    def test_entity_type_specific_resolution(self) -> None:
        resolver = EntityResolver()
        # "diffusion" resolves as methodology but not as anything else
        assert resolver.resolve("diffusion", "methodology") == "Diffusion"
        assert resolver.resolve("diffusion", "dataset") == "diffusion"  # no alias

    def test_empty_string_returns_empty(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("", "institution") == ""
        assert resolver.resolve("   ", "methodology") == ""

    def test_multiple_variants_map_to_same_canonical(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("facebook ai research", "institution") == "Meta"
        assert resolver.resolve("fair", "institution") == "Meta"
        assert resolver.resolve("meta ai", "institution") == "Meta"

    def test_methodology_aliases(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("cnn", "methodology") == "CNN"
        assert resolver.resolve("reinforcement learning", "methodology") == "Reinforcement Learning"
        assert resolver.resolve("rl", "methodology") == "Reinforcement Learning"

    def test_dataset_aliases(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("imagenet", "dataset") == "ImageNet"
        assert resolver.resolve("coco", "dataset") == "COCO"

    def test_technology_aliases(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("pytorch", "technology") == "PyTorch"
        assert resolver.resolve("tf", "technology") == "TensorFlow"

    def test_metric_aliases(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve("f1 score", "metric") == "F1"
        assert resolver.resolve("bleu", "metric") == "BLEU"


# ======================================================================
# ResearchGraph domain models
# ======================================================================


class TestResearchGraph:
    def test_empty_graph(self) -> None:
        g = ResearchGraph()
        assert g.paper_count == 0
        assert g.years == []
        assert g.year_index(2024) == []

    def test_paper_count(self) -> None:
        g = ResearchGraph(
            papers={
                "p1": PaperNode(id="p1", title="A"),
                "p2": PaperNode(id="p2", title="B"),
            }
        )
        assert g.paper_count == 2

    def test_years_property(self) -> None:
        g = ResearchGraph(
            papers={
                "p1": PaperNode(id="p1", title="A", year=2022),
                "p2": PaperNode(id="p2", title="B", year=2024),
                "p3": PaperNode(id="p3", title="C", year=2023),
                "p4": PaperNode(id="p4", title="D"),  # no year
            }
        )
        assert g.years == [2022, 2023, 2024]

    def test_year_index(self) -> None:
        p1 = PaperNode(id="p1", title="A", year=2024)
        p2 = PaperNode(id="p2", title="B", year=2023)
        p3 = PaperNode(id="p3", title="C", year=2024)
        g = ResearchGraph(papers={"p1": p1, "p2": p2, "p3": p3})
        assert g.year_index(2024) == [p1, p3]
        assert g.year_index(2023) == [p2]
        assert g.year_index(2025) == []

    def test_services_defaults_to_none(self) -> None:
        g = ResearchGraph()
        assert g.services.co_occurrence is None


class TestPaperNode:
    def test_minimal_construction(self) -> None:
        p = PaperNode(id="p1", title="Test Paper")
        assert p.id == "p1"
        assert p.title == "Test Paper"
        assert p.year is None
        assert p.authors == []
        assert p.methodologies == []

    def test_full_construction(self) -> None:
        meth = MethodologyNode(name="Transformer")
        auth = AuthorNode(name="Alice")
        p = PaperNode(
            id="p1",
            title="Test",
            year=2024,
            citation_count=42,
            venue="NeurIPS",
            authors=[auth],
            methodologies=[meth],
            techniques=["attention", "pre-training"],
        )
        assert p.year == 2024
        assert p.citation_count == 42
        assert p.venue == "NeurIPS"
        assert p.authors[0] is auth
        assert p.methodologies[0] is meth
        assert p.techniques == ["attention", "pre-training"]


class TestAuthorNode:
    def test_minimal_construction(self) -> None:
        a = AuthorNode(name="Alice")
        assert a.name == "Alice"
        assert a.paper_ids == []
        assert a.first_publication_year is None

    def test_first_publication_year(self) -> None:
        a = AuthorNode(name="Alice", paper_ids=["p1", "p2"], first_publication_year=2020)
        assert a.first_publication_year == 2020


class TestInstitutionNode:
    def test_classification_default(self) -> None:
        inst = InstitutionNode(name="Some Lab")
        assert inst.type == InstitutionType.OTHER

    def test_explicit_type(self) -> None:
        inst = InstitutionNode(name="MIT", type=InstitutionType.UNIVERSITY)
        assert inst.type == InstitutionType.UNIVERSITY


class TestMethodologyNode:
    def test_construction(self) -> None:
        m = MethodologyNode(name="Transformer", paper_ids=["p1", "p2"])
        assert m.name == "Transformer"
        assert m.paper_ids == ["p1", "p2"]


class TestDatasetNode:
    def test_construction(self) -> None:
        d = DatasetNode(name="ImageNet", paper_ids=["p1"])
        assert d.name == "ImageNet"
        assert d.paper_ids == ["p1"]


class TestTechnologyNode:
    def test_default_type(self) -> None:
        t = TechnologyNode(name="SomeTool")
        assert t.type == TechnologyType.OTHER

    def test_framework_type(self) -> None:
        t = TechnologyNode(name="PyTorch", type=TechnologyType.FRAMEWORK)
        assert t.type == TechnologyType.FRAMEWORK


class TestMetricNode:
    def test_construction(self) -> None:
        m = MetricNode(name="BLEU", paper_ids=["p1"])
        assert m.name == "BLEU"
        assert m.paper_ids == ["p1"]


# ======================================================================
# ResearchGraphBuilder
# ======================================================================


class TestResearchGraphBuilder:
    def test_build_empty_records(self) -> None:
        builder = ResearchGraphBuilder()
        graph = builder.build([])
        assert graph.paper_count == 0
        assert graph.authors == {}
        assert graph.methodologies == {}

    def test_build_single_record_with_methodology(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID, methodology="Transformer")]
        graph = builder.build(records)
        assert graph.paper_count == 1
        assert "transformer" in graph.methodologies
        assert graph.methodologies["transformer"].paper_ids == [P1_STR]
        assert graph.papers[P1_STR].methodologies[0] is graph.methodologies["transformer"]

    def test_build_single_record_with_techniques(self) -> None:
        builder = ResearchGraphBuilder()
        records = [
            _fake_record(
                paper_id=P1_UUID,
                methodology="CNN",
                techniques=["transfer learning", "data augmentation"],
            )
        ]
        graph = builder.build(records)
        # Techniques are indexed as methodologies (stemmed: "transfer learn", "data augmenta")
        assert "cnn" in graph.methodologies
        # "transfer learning" → resolve → "transfer learning" (no alias) → stem → "transfer learn"
        # "data augmentation" → resolve → "data augmentation" (no alias) → stem → "data augmenta"
        assert "transfer learn" in graph.methodologies
        assert "data augmenta" in graph.methodologies

    def test_build_with_paper_map_includes_author_nodes(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID)]
        paper_map = {
            P1_STR: PaperMetadata(
                year=2024,
                citation_count=42,
                venue="NeurIPS",
                authors=["Alice Smith", "Bob Jones"],
            ),
        }
        graph = builder.build(records, paper_map=paper_map)
        assert "Alice Smith" in graph.authors
        assert graph.authors["Alice Smith"].paper_ids == [P1_STR]
        assert graph.authors["Alice Smith"].first_publication_year == 2024
        assert "Bob Jones" in graph.authors

        # Object references
        paper = graph.papers[P1_STR]
        assert paper.year == 2024
        assert paper.citation_count == 42
        assert paper.venue == "NeurIPS"
        assert len(paper.authors) == 2
        assert paper.authors[0] is graph.authors["Alice Smith"]
        assert paper.authors[1] is graph.authors["Bob Jones"]

    def test_author_back_references_are_strings(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID), _fake_record(paper_id=P2_UUID)]
        paper_map = {
            P1_STR: PaperMetadata(authors=["Alice"]),
            P2_STR: PaperMetadata(authors=["Alice", "Bob"]),
        }
        graph = builder.build(records, paper_map=paper_map)
        # AuthorNode.paper_ids should be strings, not PaperNode references
        alice = graph.authors["Alice"]
        assert alice.paper_ids == [P1_STR, P2_STR]
        assert all(isinstance(pid, str) for pid in alice.paper_ids)
        assert all(isinstance(pid, str) for pid in alice.paper_ids)

    def test_deduplicates_techniques(self) -> None:
        builder = ResearchGraphBuilder()
        records = [
            _fake_record(
                paper_id=P1_UUID,
                techniques=["cnn", "CNN", "  cnn  "],
            )
        ]
        graph = builder.build(records)
        # All three variants → normalize("cnn") → "cnn" → resolve("cnn", "methodology") → "CNN"
        assert "CNN" in graph.methodologies
        assert graph.methodologies["CNN"].paper_ids == [P1_STR]

    def test_institution_classification(self) -> None:
        builder = ResearchGraphBuilder()
        assert builder._classify_institution("MIT") == InstitutionType.UNIVERSITY
        assert builder._classify_institution("Google") == InstitutionType.COMPANY
        assert (
            builder._classify_institution(
                "National Institutes of Health",
            )
            == InstitutionType.GOVERNMENT
        )
        assert builder._classify_institution("Some Research Lab") == InstitutionType.LAB
        assert builder._classify_institution("Unknown Organization") == InstitutionType.OTHER

    def test_technology_classification(self) -> None:
        builder = ResearchGraphBuilder()
        assert builder._classify_technology("PyTorch") == TechnologyType.FRAMEWORK
        assert builder._classify_technology("NumPy") == TechnologyType.LIBRARY
        assert builder._classify_technology("CUDA") == TechnologyType.TOOL
        assert builder._classify_technology("Custom Script") == TechnologyType.OTHER

    def test_services_attached(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID)]
        graph = builder.build(records)
        assert graph.services is not None
        assert isinstance(graph.services.co_occurrence, CoOccurrenceService)
        assert isinstance(graph.services.trends, TrendService)
        assert isinstance(graph.services.similarity, SimilarityService)
        assert isinstance(graph.services.centrality, CentralityService)
        assert isinstance(graph.services.statistics, StatisticsService)

    def test_normalisation_uses_resolver(self) -> None:
        builder = ResearchGraphBuilder()
        records = [
            _fake_record(
                paper_id=P1_UUID,
                methodology="reinforcement learning",
            )
        ]
        graph = builder.build(records)
        # resolve("reinforcement learning", "methodology") → "Reinforcement Learning"
        # stem("Reinforcement Learning") → "reinforcement learn"
        assert "reinforcement learn" in graph.methodologies
        # stemmed storage is expected because the normalizer applies after resolution

    def test_multiple_papers_same_methodology(self) -> None:
        builder = ResearchGraphBuilder()
        records = [
            _fake_record(paper_id=P1_UUID, methodology="Transformer"),
            _fake_record(paper_id=P2_UUID, methodology="Transformer"),
            _fake_record(paper_id=P3_UUID, methodology="CNN"),
        ]
        graph = builder.build(records)
        assert "transformer" in graph.methodologies
        assert graph.methodologies["transformer"].paper_ids == [P1_STR, P2_STR]
        assert graph.methodologies["cnn"].paper_ids == [P3_STR]

    def test_no_cross_reference_for_unknown_author(self) -> None:
        """Authors not in paper_map should not create AuthorNode."""
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID)]
        graph = builder.build(records)
        # No paper_map → no author_name → no AuthorNode
        assert graph.authors == {}

    def test_record_without_methodology(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID, methodology=None)]
        graph = builder.build(records)
        assert graph.paper_count == 1
        assert len(graph.methodologies) == 0

    def test_future_field_graceful_handling(self) -> None:
        """Builder should not crash when Sprint 2.1 fields don't exist."""
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID, methodology="Transformer")]
        graph = builder.build(records)
        assert graph.paper_count == 1
        assert "transformer" in graph.methodologies

    def test_paper_has_techniques_and_limitations(self) -> None:
        builder = ResearchGraphBuilder()
        records = [
            _fake_record(
                paper_id=P1_UUID,
                techniques=["attention"],
                limitations=["computational cost"],
            )
        ]
        graph = builder.build(records)
        paper = graph.papers[P1_STR]
        # "attention" → normalize → "atten" (light stem strips "tion")
        # → resolve("atten", "methodology") → no alias → "atten"
        assert "atten" in paper.techniques
        # "computational cost" → normalize → "computational cost" (no change from stemmer)
        assert "computational cost" in paper.limitations


# ======================================================================
# AnalysisContext
# ======================================================================


class TestAnalysisContext:
    def test_minimal_construction(self) -> None:
        config = IntelligenceConfig()
        graph = ResearchGraph()
        ctx = AnalysisContext(
            graph=graph,
            config=config,
            investigation_id="inv-1",
        )
        assert ctx.graph is graph
        assert ctx.config is config
        assert ctx.investigation_id == "inv-1"
        assert ctx.execution_id is None
        assert ctx.logger is None

    def test_full_construction(self) -> None:
        config = IntelligenceConfig()
        graph = ResearchGraph()
        ctx = AnalysisContext(
            graph=graph,
            config=config,
            investigation_id="inv-1",
            execution_id="exec-1",
            logger="mock-logger",
        )
        assert ctx.execution_id == "exec-1"
        assert ctx.logger == "mock-logger"


# ======================================================================
# IntelligenceConfig
# ======================================================================


class TestIntelligenceConfig:
    def test_default_values(self) -> None:
        cfg = IntelligenceConfig()
        assert cfg.min_methodology_frequency == 1
        assert cfg.min_dataset_frequency == 1
        assert cfg.min_technology_frequency == 1
        assert cfg.min_author_frequency == 1
        assert cfg.trend_window_years == 3
        assert cfg.co_occurrence_threshold == 1
        assert cfg.novelty_std_threshold == 2.0
        assert cfg.max_results_per_analyzer == 20

    def test_custom_values(self) -> None:
        cfg = IntelligenceConfig(
            min_methodology_frequency=3,
            trend_window_years=5,
            novelty_std_threshold=1.5,
            max_results_per_analyzer=50,
        )
        assert cfg.min_methodology_frequency == 3
        assert cfg.trend_window_years == 5
        assert cfg.novelty_std_threshold == 1.5
        assert cfg.max_results_per_analyzer == 50


# ======================================================================
# Helpers
# ======================================================================


def _fake_record(
    paper_id: uuid.UUID = P1_UUID,
    paper_title: str = "Test Paper",
    methodology: str | None = "Transformer",
    techniques: list[str] | None = None,
    limitations: list[str] | None = None,
    future_work: list[str] | None = None,
    key_findings: list[str] | None = None,
    key_contributions: list[str] | None = None,
    cited_works: list[str] | None = None,
) -> FakeKnowledge:
    """Create a minimal fake ``ExtractedKnowledge``-like object."""
    return FakeKnowledge(
        paper_id=paper_id,
        paper_title=paper_title,
        methodology=methodology,
        relevant_techniques=techniques or [],
        limitations=limitations or [],
        future_work=future_work or [],
        key_findings=key_findings or [],
        key_contributions=key_contributions or [],
        cited_works=cited_works or [],
    )


@dataclass
class FakeKnowledge:
    """Minimum viable fake for ``ExtractedKnowledge``.

    Only exposes fields that ``ResearchGraphBuilder`` actually reads.
    """

    paper_id: uuid.UUID
    paper_title: str = ""
    methodology: str | None = None
    relevant_techniques: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    future_work: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    key_contributions: list[str] = field(default_factory=list)
    cited_works: list[str] = field(default_factory=list)

    # Sprint 2.1 forward-compatible fields (optional)
    institutions: list[Any] | None = None
    evaluation_metrics: list[Any] | None = None
    datasets_used: list[Any] | None = None
    technologies: list[Any] | None = None
    research_domains: list[str] | None = None
