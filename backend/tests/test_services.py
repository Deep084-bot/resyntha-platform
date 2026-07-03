"""Unit tests for GraphServices implementations (Sprint 2.3).

Covers:
  - CoOccurrenceService
  - TrendService
  - StatisticsService
  - CentralityService
"""

from __future__ import annotations

import pytest

from app.modules.intelligence import (
    AuthorNode,
    InstitutionNode,
    InstitutionType,
    MethodologyNode,
    PaperNode,
    ResearchGraph,
    TechnologyNode,
    TechnologyType,
)
from app.modules.intelligence.services.centrality import CentralityService
from app.modules.intelligence.services.co_occurrence import CoOccurrenceService
from app.modules.intelligence.services.statistics import StatisticsService
from app.modules.intelligence.services.trends import TrendService

# ── Helpers ─────────────────────────────────────────────────────────

P1, P2, P3 = "p1", "p2", "p3"


def _paper(id: str, year: int | None = None) -> PaperNode:
    return PaperNode(id=id, title="", year=year)


def _graph(**overrides: dict) -> ResearchGraph:
    kwargs = {
        "papers": {},
        "authors": {},
        "institutions": {},
        "methodologies": {},
        "datasets": {},
        "technologies": {},
        "metrics": {},
    }
    kwargs.update(overrides)
    graph = ResearchGraph(**kwargs)
    graph.services.co_occurrence = CoOccurrenceService(graph)
    graph.services.trends = TrendService(graph)
    graph.services.statistics = StatisticsService(graph)
    graph.services.centrality = CentralityService(graph)
    return graph


# ======================================================================
# CoOccurrenceService
# ======================================================================


class TestCoOccurrenceService:
    def test_between_same_type(self) -> None:
        graph = _graph(
            technologies={
                "PyTorch": TechnologyNode(
                    name="PyTorch", type=TechnologyType.FRAMEWORK,
                    paper_ids=[P1, P2],
                ),
                "TensorFlow": TechnologyNode(
                    name="TensorFlow", type=TechnologyType.FRAMEWORK,
                    paper_ids=[P1, P2, P3],
                ),
            },
        )
        svc = graph.services.co_occurrence
        assert svc.between("technology", "PyTorch", "technology", "TensorFlow") == 2
        assert svc.between("technology", "PyTorch", "technology", "PyTorch") == 2

    def test_between_cross_type(self) -> None:
        graph = _graph(
            papers={"p1": _paper("p1")},
            technologies={
                "PyTorch": TechnologyNode(
                    name="PyTorch", type=TechnologyType.FRAMEWORK,
                    paper_ids=[P1],
                ),
            },
            methodologies={
                "CNN": MethodologyNode(name="CNN", paper_ids=[P1]),
            },
        )
        svc = graph.services.co_occurrence
        assert svc.between("technology", "PyTorch", "methodology", "CNN") == 1

    def test_between_no_overlap(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P2]),
            },
        )
        svc = graph.services.co_occurrence
        assert svc.between("technology", "A", "technology", "B") == 0

    def test_between_nonexistent_entity(self) -> None:
        graph = _graph()
        svc = graph.services.co_occurrence
        assert svc.between("technology", "Nope", "technology", "AlsoNope") == 0

    def test_matrix_all(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P2, P3]),
                "C": TechnologyNode(name="C", type=TechnologyType.OTHER, paper_ids=[P1]),
            },
        )
        svc = graph.services.co_occurrence
        mat = svc.matrix("technology")
        assert mat["A"]["B"] == 1
        assert mat["B"]["A"] == 1
        assert mat["A"]["C"] == 1
        assert "B" not in mat["C"]
        assert "A" not in mat["A"]

    def test_matrix_subset(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1]),
                "B": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1]),
            },
        )
        svc = graph.services.co_occurrence
        # Use only one entity — no co-occurrence possible
        mat = svc.matrix("technology", names=["A"])
        assert mat == {"A": {}}

    def test_matrix_empty(self) -> None:
        graph = _graph()
        svc = graph.services.co_occurrence
        assert svc.matrix("technology") == {}

    def test_top_co_occurring(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P1, P2, P3]),
                "C": TechnologyNode(name="C", type=TechnologyType.OTHER, paper_ids=[P1]),
            },
        )
        svc = graph.services.co_occurrence
        top = svc.top_co_occurring("technology", "A")
        assert top[0][0] == "B"
        assert top[0][1] == 2
        assert len(top) >= 1

    def test_top_co_occurring_respects_n(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P1]),
                "C": TechnologyNode(name="C", type=TechnologyType.OTHER, paper_ids=[P2]),
            },
        )
        svc = graph.services.co_occurrence
        top = svc.top_co_occurring("technology", "A", n=1)
        assert len(top) == 1

    def test_top_co_occurring_nonexistent(self) -> None:
        graph = _graph()
        svc = graph.services.co_occurrence
        assert svc.top_co_occurring("technology", "Nope") == []


# ======================================================================
# TrendService
# ======================================================================


class TestTrendService:
    def test_year_over_year_single_year(self) -> None:
        graph = _graph(
            papers={"p1": _paper("p1", year=2023)},
            technologies={
                "PyTorch": TechnologyNode(
                    name="PyTorch", type=TechnologyType.FRAMEWORK, paper_ids=["p1"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.year_over_year("technology", "PyTorch") == {2023: 1}

    def test_year_over_year_multiple_years(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2024),
                "p3": _paper("p3", year=2024),
            },
            technologies={
                "PyTorch": TechnologyNode(
                    name="PyTorch", type=TechnologyType.FRAMEWORK,
                    paper_ids=["p1", "p2", "p3"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.year_over_year("technology", "PyTorch") == {2023: 1, 2024: 2}

    def test_year_over_year_nonexistent(self) -> None:
        graph = _graph()
        svc = graph.services.trends
        assert svc.year_over_year("technology", "Nope") == {}

    def test_first_year(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2022),
                "p2": _paper("p2", year=2024),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER, paper_ids=["p1", "p2"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.first_year("technology", "T") == 2022

    def test_first_year_nonexistent(self) -> None:
        graph = _graph()
        svc = graph.services.trends
        assert svc.first_year("technology", "Nope") is None

    def test_growth_rate_positive(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2024),
                "p3": _paper("p3", year=2024),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER, paper_ids=["p1", "p2", "p3"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.growth_rate("technology", "T") == pytest.approx(1.0)

    def test_growth_rate_negative(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2023),
                "p1b": _paper("p1b", year=2023),
                "p2": _paper("p2", year=2024),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER,
                    paper_ids=["p1", "p1b", "p2"],
                ),
            },
        )
        svc = graph.services.trends
        # 2023: 2 papers, 2024: 1 paper → growth = (1-2)/2 = -0.5
        assert svc.growth_rate("technology", "T") == pytest.approx(-0.5)

    def test_growth_rate_insufficient_data(self) -> None:
        graph = _graph(
            papers={"p1": _paper("p1", year=2023)},
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER, paper_ids=["p1"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.growth_rate("technology", "T") == 0.0

    def test_is_emerging_true(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2024),
                "p2": _paper("p2", year=2025),
                "p3": _paper("p3", year=2025),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER, paper_ids=["p1", "p2", "p3"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.is_emerging("technology", "T", recent_years=2)

    def test_is_emerging_false_when_not_recent(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2020),
                "p2": _paper("p2", year=2020),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER, paper_ids=["p1", "p2"],
                ),
            },
        )
        svc = graph.services.trends
        assert not svc.is_emerging("technology", "T", recent_years=2)

    def test_is_declining_true(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2023),
                "p1b": _paper("p1b", year=2023),
                "p2": _paper("p2", year=2024),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER,
                    paper_ids=["p1", "p1b", "p2"],
                ),
            },
        )
        svc = graph.services.trends
        assert svc.is_declining("technology", "T")

    def test_is_declining_false_when_growing(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2024),
                "p3": _paper("p3", year=2024),
            },
            technologies={
                "T": TechnologyNode(
                    name="T", type=TechnologyType.OTHER,
                    paper_ids=["p1", "p2", "p3"],
                ),
            },
        )
        svc = graph.services.trends
        assert not svc.is_declining("technology", "T")

    def test_top_emerging(self) -> None:
        graph = _graph(
            papers={
                "p1": _paper("p1", year=2024),
                "p2": _paper("p2", year=2025),
                "p3": _paper("p3", year=2025),
                "p4": _paper("p4", year=2024),
                "p5": _paper("p5", year=2025),
            },
            technologies={
                "Growing": TechnologyNode(
                    name="Growing", type=TechnologyType.OTHER,
                    paper_ids=["p1", "p2", "p3"],
                ),
                "Flat": TechnologyNode(
                    name="Flat", type=TechnologyType.OTHER,
                    paper_ids=["p4", "p5"],
                ),
            },
        )
        svc = graph.services.trends
        emerging = svc.top_emerging("technology", n=5, recent_years=2)
        names = [name for name, _ in emerging]
        assert "Growing" in names

    def test_top_emerging_empty(self) -> None:
        graph = _graph()
        svc = graph.services.trends
        assert svc.top_emerging("technology") == []


# ======================================================================
# StatisticsService
# ======================================================================


class TestStatisticsService:
    def test_frequency_distribution_raw(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P1]),
            },
        )
        svc = graph.services.statistics
        raw = svc.frequency_distribution("technology", normalize=False)
        assert raw["A"] == 2
        assert raw["B"] == 1

    def test_frequency_distribution_normalized(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
            },
        )
        svc = graph.services.statistics
        norm = svc.frequency_distribution("technology", normalize=True)
        assert norm["B"] == pytest.approx(2 / 3)

    def test_frequency_distribution_empty(self) -> None:
        graph = _graph()
        svc = graph.services.statistics
        assert svc.frequency_distribution("technology") == {}

    def test_top_n(self) -> None:
        graph = _graph(
            technologies={
                "A": TechnologyNode(name="A", type=TechnologyType.OTHER, paper_ids=[P1]),
                "B": TechnologyNode(name="B", type=TechnologyType.OTHER, paper_ids=[P1, P2, P3]),
                "C": TechnologyNode(name="C", type=TechnologyType.OTHER, paper_ids=[P1, P2]),
            },
        )
        svc = graph.services.statistics
        top = svc.top_n("technology", n=2)
        assert top[0][0] == "B"
        assert top[1][0] == "C"

    def test_top_n_respects_limit(self) -> None:
        graph = _graph(
            technologies={
                f"T{i}": TechnologyNode(
                    name=f"T{i}", type=TechnologyType.OTHER, paper_ids=[f"p{i}"],
                )
                for i in range(5)
            },
        )
        svc = graph.services.statistics
        assert len(svc.top_n("technology", n=3)) == 3

    def test_top_n_empty(self) -> None:
        graph = _graph()
        svc = graph.services.statistics
        assert svc.top_n("technology") == []

    def test_z_scores(self) -> None:
        svc = StatisticsService(_graph())
        scores = svc.z_scores([1.0, 2.0, 3.0])
        assert len(scores) == 3
        assert scores[0] == pytest.approx(-1.0)
        assert scores[1] == pytest.approx(0.0)
        assert scores[2] == pytest.approx(1.0)

    def test_z_scores_single_value(self) -> None:
        svc = StatisticsService(_graph())
        assert svc.z_scores([5.0]) == [0.0]

    def test_z_scores_empty(self) -> None:
        svc = StatisticsService(_graph())
        assert svc.z_scores([]) == []

    def test_percentile(self) -> None:
        svc = StatisticsService(_graph())
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert svc.percentile(vals, 50) == pytest.approx(3.0)
        assert svc.percentile(vals, 0) == pytest.approx(1.0)
        assert svc.percentile(vals, 100) == pytest.approx(5.0)

    def test_percentile_empty(self) -> None:
        svc = StatisticsService(_graph())
        assert svc.percentile([], 50) == 0.0


# ======================================================================
# CentralityService
# ======================================================================


class TestCentralityService:
    def test_co_authorship_edges(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    authors=[
                        AuthorNode(name="Alice"),
                        AuthorNode(name="Bob"),
                    ],
                ),
            },
        )
        svc = graph.services.centrality
        edges = svc.co_authorship_edges()
        assert ("Alice", "Bob", 1) in edges or ("Bob", "Alice", 1) in edges

    def test_co_authorship_edges_weight(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    authors=[AuthorNode(name="Alice"), AuthorNode(name="Bob")],
                ),
                P2: PaperNode(
                    id=P2, title="",
                    authors=[AuthorNode(name="Alice"), AuthorNode(name="Bob")],
                ),
            },
        )
        svc = graph.services.centrality
        edges = svc.co_authorship_edges()
        for a, b, w in edges:
            if "Alice" in (a, b) and "Bob" in (a, b):
                assert w == 2
                break
        else:
            pytest.fail("Alice-Bob edge not found")

    def test_co_authorship_edges_empty(self) -> None:
        graph = _graph()
        svc = graph.services.centrality
        assert svc.co_authorship_edges() == []

    def test_collaboration_edges(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    institutions=[
                        InstitutionNode(name="MIT", type=InstitutionType.UNIVERSITY),
                        InstitutionNode(name="Stanford", type=InstitutionType.UNIVERSITY),
                    ],
                ),
            },
        )
        svc = graph.services.centrality
        edges = svc.collaboration_edges()
        assert ("MIT", "Stanford", 1) in edges or ("Stanford", "MIT", 1) in edges

    def test_collaboration_edges_weight(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    institutions=[
                        InstitutionNode(name="MIT", type=InstitutionType.UNIVERSITY),
                        InstitutionNode(name="Stanford", type=InstitutionType.UNIVERSITY),
                    ],
                ),
                P2: PaperNode(
                    id=P2, title="",
                    institutions=[
                        InstitutionNode(name="MIT", type=InstitutionType.UNIVERSITY),
                        InstitutionNode(name="Stanford", type=InstitutionType.UNIVERSITY),
                    ],
                ),
            },
        )
        svc = graph.services.centrality
        edges = svc.collaboration_edges()
        for a, b, w in edges:
            if "MIT" in (a, b) and "Stanford" in (a, b):
                assert w == 2
                break
        else:
            pytest.fail("MIT-Stanford edge not found")

    def test_collaboration_edges_empty(self) -> None:
        graph = _graph()
        svc = graph.services.centrality
        assert svc.collaboration_edges() == []

    def test_degree_centrality_author(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    authors=[AuthorNode(name="Alice"), AuthorNode(name="Bob")],
                ),
                P2: PaperNode(
                    id=P2, title="",
                    authors=[AuthorNode(name="Alice"), AuthorNode(name="Charlie")],
                ),
            },
        )
        svc = graph.services.centrality
        cent = svc.degree_centrality("author")
        assert cent["Alice"] == pytest.approx(1.0)
        assert cent["Bob"] == pytest.approx(0.5)
        assert cent["Charlie"] == pytest.approx(0.5)

    def test_degree_centrality_institution(self) -> None:
        graph = _graph(
            papers={
                P1: PaperNode(
                    id=P1, title="",
                    institutions=[
                        InstitutionNode(name="MIT", type=InstitutionType.UNIVERSITY),
                        InstitutionNode(name="Stanford", type=InstitutionType.UNIVERSITY),
                    ],
                ),
            },
        )
        svc = graph.services.centrality
        cent = svc.degree_centrality("institution")
        assert cent["MIT"] == pytest.approx(1.0)
        assert cent["Stanford"] == pytest.approx(1.0)

    def test_degree_centrality_empty(self) -> None:
        graph = _graph()
        svc = graph.services.centrality
        assert svc.degree_centrality("author") == {}
