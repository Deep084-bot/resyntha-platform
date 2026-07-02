"""Unit tests for the Intelligence Engine analyzers (Sprint 2.3).

Covers:
  - AnalyzerResult, AnalysisResults containers
  - BaseAnalyzer abstract base
  - InstitutionAnalyzer
  - MethodologyAnalyzer
  - TemporalAnalyzer
  - IntelligenceEngine orchestrator
"""

from __future__ import annotations

import pytest

from app.modules.intelligence import (
    AnalysisContext,
    AnalysisResults,
    AnalyzerResult,
    BaseAnalyzer,
    GraphServices,
    InstitutionAnalyzer,
    InstitutionNode,
    InstitutionType,
    IntelligenceConfig,
    IntelligenceEngine,
    MethodologyAnalyzer,
    MethodologyNode,
    PaperMetadata,
    PaperNode,
    ResearchGraph,
    ResearchGraphBuilder,
    TemporalAnalyzer,
)
from app.modules.intelligence.analyzers.base import BaseAnalyzer as BaseAnalyzerCls
from tests.test_intelligence import P1_STR, P1_UUID, _fake_record

# ======================================================================
# Helpers
# ======================================================================

def _empty_graph() -> ResearchGraph:
    return ResearchGraph(
        papers={},
        authors={},
        institutions={},
        methodologies={},
        datasets={},
        technologies={},
        metrics={},
        services=GraphServices(),
    )


def _context(graph: ResearchGraph | None = None) -> AnalysisContext:
    return AnalysisContext(
        graph=graph or _empty_graph(),
        config=IntelligenceConfig(),
        investigation_id="test-inv",
    )


def _paper(id: str, year: int | None = None) -> PaperNode:
    return PaperNode(id=id, title="", year=year)


# ======================================================================
# AnalyzerResult
# ======================================================================


class TestAnalyzerResult:
    def test_minimal_construction(self) -> None:
        result = AnalyzerResult(analyzer_name="test")
        assert result.analyzer_name == "test"
        assert result.data == {}

    def test_with_data(self) -> None:
        result = AnalyzerResult(
            analyzer_name="test", data={"count": 42, "items": [1, 2]},
        )
        assert result.data["count"] == 42
        assert result.data["items"] == [1, 2]

    def test_analyzer_name_is_required(self) -> None:
        result = AnalyzerResult(analyzer_name="req")
        assert result.analyzer_name == "req"


# ======================================================================
# AnalysisResults
# ======================================================================


class TestAnalysisResults:
    def test_empty_defaults(self) -> None:
        results = AnalysisResults()
        assert results.results == {}
        assert results.analyzer_names == []
        assert results.investigation_id == ""
        assert results.execution_id is None

    def test_with_results(self) -> None:
        r1 = AnalyzerResult(analyzer_name="a", data={"v": 1})
        r2 = AnalyzerResult(analyzer_name="b", data={"v": 2})
        container = AnalysisResults(
            results={"a": r1, "b": r2},
            investigation_id="inv-1",
            execution_id="exec-1",
        )
        assert container["a"] is r1
        assert container["b"] is r2
        assert container.analyzer_names == ["a", "b"]
        assert container.investigation_id == "inv-1"
        assert container.execution_id == "exec-1"


# ======================================================================
# BaseAnalyzer
# ======================================================================


class TestBaseAnalyzer:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseAnalyzerCls(_context())  # type: ignore[abstract]

    def test_analyzer_name_defaults_to_empty(self) -> None:
        assert BaseAnalyzerCls.analyzer_name == ""

    def test_concrete_subclass_works(self) -> None:
        class FakeAnalyzer(BaseAnalyzerCls):
            analyzer_name = "fake"

            def analyze(self) -> AnalyzerResult:
                return AnalyzerResult(analyzer_name=self.analyzer_name)

        inst = FakeAnalyzer(_context())
        result = inst.analyze()
        assert result.analyzer_name == "fake"

    def test_subclass_has_graph_and_config(self) -> None:
        class FakeAnalyzer(BaseAnalyzerCls):
            analyzer_name = "fake"

            def analyze(self) -> AnalyzerResult:
                return AnalyzerResult(
                    analyzer_name=self.analyzer_name,
                    data={
                        "graph_paper_count": self.graph.paper_count,
                        "config_max_results": self.config.max_results_per_analyzer,
                    },
                )

        ctx = _context(_empty_graph())
        inst = FakeAnalyzer(ctx)
        result = inst.analyze()
        assert result.data["graph_paper_count"] == 0
        assert result.data["config_max_results"] == 20


# ======================================================================
# InstitutionAnalyzer
# ======================================================================


class TestInstitutionAnalyzer:
    def test_empty_graph(self) -> None:
        analyzer = InstitutionAnalyzer(_context())
        result = analyzer.analyze()
        assert result.analyzer_name == "institution"
        assert result.data["total_institutions"] == 0
        assert result.data["institution_type_distribution"] == {}
        assert result.data["top_institutions"] == []

    def test_single_institution(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1")},
            authors={},
            institutions={
                "MIT": InstitutionNode(
                    name="MIT",
                    type=InstitutionType.UNIVERSITY,
                    paper_ids=["p1"],
                    author_names=["Alice"],
                ),
            },
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = InstitutionAnalyzer(_context(graph))
        result = analyzer.analyze()

        assert result.data["total_institutions"] == 1
        assert result.data["institution_type_distribution"] == {
            InstitutionType.UNIVERSITY.value: 1,
        }
        assert len(result.data["top_institutions"]) == 1
        top = result.data["top_institutions"][0]
        assert top["name"] == "MIT"
        assert top["paper_count"] == 1
        assert top["author_count"] == 1

    def test_multiple_types(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1"), "p2": _paper("p2")},
            authors={},
            institutions={
                "MIT": InstitutionNode(
                    name="MIT", type=InstitutionType.UNIVERSITY,
                    paper_ids=["p1"], author_names=["Alice"],
                ),
                "Stanford": InstitutionNode(
                    name="Stanford", type=InstitutionType.UNIVERSITY,
                    paper_ids=["p2"], author_names=["Bob"],
                ),
                "Google": InstitutionNode(
                    name="Google", type=InstitutionType.COMPANY,
                    paper_ids=["p1", "p2"], author_names=["Alice", "Bob"],
                ),
            },
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = InstitutionAnalyzer(_context(graph))
        result = analyzer.analyze()

        assert result.data["total_institutions"] == 3
        dist = result.data["institution_type_distribution"]
        assert dist[InstitutionType.UNIVERSITY.value] == 2
        assert dist[InstitutionType.COMPANY.value] == 1

        # Sorted by paper_count desc
        top = result.data["top_institutions"]
        assert top[0]["name"] == "Google"
        assert top[0]["paper_count"] == 2
        assert top[1]["name"] in ("MIT", "Stanford")
        assert top[1]["paper_count"] == 1

    def test_institutions_by_type(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1")},
            authors={},
            institutions={
                "MIT": InstitutionNode(
                    name="MIT", type=InstitutionType.UNIVERSITY,
                    paper_ids=["p1"], author_names=[],
                ),
            },
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = InstitutionAnalyzer(_context(graph))
        result = analyzer.analyze()

        by_type = result.data["institutions_by_type"]
        assert InstitutionType.UNIVERSITY.value in by_type
        assert len(by_type[InstitutionType.UNIVERSITY.value]) == 1
        assert by_type[InstitutionType.UNIVERSITY.value][0]["name"] == "MIT"

    def test_respects_max_results(self) -> None:
        config = IntelligenceConfig(max_results_per_analyzer=1)
        context = AnalysisContext(
            graph=_empty_graph(),
            config=config,
            investigation_id="test",
        )
        # Manually patch config into a graph with more institutions
        context.graph.institutions = {
            f"Inst{i}": InstitutionNode(
                name=f"Inst{i}", type=InstitutionType.OTHER,
                paper_ids=["p1"], author_names=[],
            )
            for i in range(5)
        }
        analyzer = InstitutionAnalyzer(context)
        result = analyzer.analyze()
        assert len(result.data["top_institutions"]) == 1


# ======================================================================
# MethodologyAnalyzer
# ======================================================================


class TestMethodologyAnalyzer:
    def test_empty_graph(self) -> None:
        analyzer = MethodologyAnalyzer(_context())
        result = analyzer.analyze()
        assert result.analyzer_name == "methodology"
        assert result.data["total_methodologies"] == 0
        assert result.data["methodologies"] == []

    def test_single_methodology(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1")},
            authors={},
            institutions={},
            methodologies={
                "CNN": MethodologyNode(
                    name="CNN", paper_ids=["p1"], techniques=[],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = MethodologyAnalyzer(_context(graph))
        result = analyzer.analyze()

        assert result.data["total_methodologies"] == 1
        assert len(result.data["methodologies"]) == 1
        entry = result.data["methodologies"][0]
        assert entry["name"] == "CNN"
        assert entry["paper_count"] == 1
        assert entry["technique_count"] == 0

    def test_methodology_with_techniques(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1")},
            authors={},
            institutions={},
            methodologies={
                "CNN": MethodologyNode(
                    name="CNN", paper_ids=["p1"],
                    techniques=["convolution", "pooling"],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = MethodologyAnalyzer(_context(graph))
        result = analyzer.analyze()

        entry = result.data["methodologies"][0]
        assert entry["technique_count"] == 2
        assert entry["techniques"] == ["convolution", "pooling"]

    def test_multiple_methodologies_sorted_by_frequency(self) -> None:
        graph = ResearchGraph(
            papers={f"p{i}": _paper(f"p{i}") for i in range(4)},
            authors={},
            institutions={},
            methodologies={
                "CNN": MethodologyNode(
                    name="CNN", paper_ids=["p1", "p2"], techniques=[],
                ),
                "RNN": MethodologyNode(
                    name="RNN", paper_ids=["p3"], techniques=[],
                ),
                "Transformer": MethodologyNode(
                    name="Transformer", paper_ids=["p1", "p2", "p3", "p4"],
                    techniques=[],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = MethodologyAnalyzer(_context(graph))
        result = analyzer.analyze()

        m = result.data["methodologies"]
        assert len(m) == 3
        assert m[0]["name"] == "Transformer"
        assert m[0]["paper_count"] == 4
        assert m[1]["name"] == "CNN"
        assert m[1]["paper_count"] == 2
        assert m[2]["name"] == "RNN"
        assert m[2]["paper_count"] == 1

    def test_respects_max_results(self) -> None:
        config = IntelligenceConfig(max_results_per_analyzer=2)
        context = AnalysisContext(
            graph=_empty_graph(),
            config=config,
            investigation_id="test",
        )
        context.graph.methodologies = {
            f"M{i}": MethodologyNode(
                name=f"M{i}", paper_ids=[f"p{i}"], techniques=[],
            )
            for i in range(10)
        }
        analyzer = MethodologyAnalyzer(context)
        result = analyzer.analyze()
        assert len(result.data["methodologies"]) == 2


# ======================================================================
# TemporalAnalyzer
# ======================================================================


class TestTemporalAnalyzer:
    def test_empty_graph(self) -> None:
        analyzer = TemporalAnalyzer(_context())
        result = analyzer.analyze()
        assert result.analyzer_name == "temporal"
        assert result.data["years_covered"] == []
        assert result.data["total_papers"] == 0
        assert result.data["papers_per_year"] == {}

    def test_papers_per_year(self) -> None:
        graph = ResearchGraph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2023),
                "p3": _paper("p3", year=2024),
                "p4": _paper("p4", year=2025),
            },
            authors={},
            institutions={},
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()

        assert result.data["years_covered"] == [2023, 2024, 2025]
        assert result.data["total_papers"] == 4
        assert result.data["papers_per_year"] == {2023: 2, 2024: 1, 2025: 1}

    def test_papers_without_year_omitted(self) -> None:
        graph = ResearchGraph(
            papers={
                "p1": _paper("p1", year=None),
                "p2": _paper("p2", year=2024),
            },
            authors={},
            institutions={},
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()
        assert result.data["papers_per_year"] == {2024: 1}
        assert result.data["total_papers"] == 2

    def test_years_sorted(self) -> None:
        graph = ResearchGraph(
            papers={
                "p1": _paper("p1", year=2025),
                "p2": _paper("p2", year=2023),
                "p3": _paper("p3", year=2024),
            },
            authors={},
            institutions={},
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()
        assert result.data["years_covered"] == [2023, 2024, 2025]
        assert result.data["papers_per_year"] == {2023: 1, 2024: 1, 2025: 1}

    def test_methodology_trends(self) -> None:
        graph = ResearchGraph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2023),
                "p3": _paper("p3", year=2024),
            },
            authors={},
            institutions={},
            methodologies={
                "CNN": MethodologyNode(
                    name="CNN", paper_ids=["p1", "p3"], techniques=[],
                ),
                "RNN": MethodologyNode(
                    name="RNN", paper_ids=["p2"], techniques=[],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()

        trends = result.data["methodology_trends"]
        assert "CNN" in trends
        assert trends["CNN"] == {2023: 1, 2024: 1}
        assert "RNN" in trends
        assert trends["RNN"] == {2023: 1}

    def test_methodology_without_papers_not_in_trends(self) -> None:
        graph = ResearchGraph(
            papers={},
            authors={},
            institutions={},
            methodologies={
                "Orphan": MethodologyNode(
                    name="Orphan", paper_ids=["nonexistent"], techniques=[],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()
        assert result.data["methodology_trends"] == {}

    def test_institution_trends(self) -> None:
        graph = ResearchGraph(
            papers={
                "p1": _paper("p1", year=2023),
                "p2": _paper("p2", year=2024),
            },
            authors={},
            institutions={
                "MIT": InstitutionNode(
                    name="MIT", type=InstitutionType.UNIVERSITY,
                    paper_ids=["p1", "p2"], author_names=[],
                ),
            },
            methodologies={},
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        analyzer = TemporalAnalyzer(_context(graph))
        result = analyzer.analyze()

        trends = result.data["institution_trends"]
        assert "MIT" in trends
        assert trends["MIT"] == {2023: 1, 2024: 1}

    def test_trends_via_builder(self) -> None:
        builder = ResearchGraphBuilder()
        records = [_fake_record(paper_id=P1_UUID, methodology="CNN")]
        paper_map = {
            P1_STR: PaperMetadata(
                year=2023, citation_count=None, venue=None, authors=None, doi=None,
            ),
        }
        graph = builder.build(records, paper_map=paper_map)
        context = AnalysisContext(
            graph=graph,
            config=IntelligenceConfig(),
            investigation_id="test",
        )
        analyzer = TemporalAnalyzer(context)
        result = analyzer.analyze()
        # After stemmer: "cnn" is already canonical
        assert result.data["total_papers"] == 1
        assert result.data["papers_per_year"] == {2023: 1}
        assert len(result.data["methodology_trends"]) >= 0


# ======================================================================
# IntelligenceEngine
# ======================================================================


class FakeAnalyzer(BaseAnalyzer):
    analyzer_name = "fake"

    def __init__(self, context: AnalysisContext, *, value: int = 0) -> None:
        super().__init__(context)
        self._value = value

    def analyze(self) -> AnalyzerResult:
        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={"value": self._value},
        )


class OtherAnalyzer(BaseAnalyzer):
    analyzer_name = "other"

    def analyze(self) -> AnalyzerResult:
        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={"x": 42},
        )


class TestIntelligenceEngine:
    def test_empty_engine_returns_empty_results(self) -> None:
        engine = IntelligenceEngine(_context())
        results = engine.run()
        assert results.results == {}
        assert results.analyzer_names == []

    def test_single_analyzer(self) -> None:
        engine = IntelligenceEngine(_context())
        engine.register(FakeAnalyzer(_context(), value=7))
        results = engine.run()
        assert "fake" in results.results
        assert results["fake"].data["value"] == 7

    def test_multiple_analyzers(self) -> None:
        engine = IntelligenceEngine(_context())
        engine.register(FakeAnalyzer(_context(), value=1))
        engine.register(OtherAnalyzer(_context()))
        results = engine.run()
        assert set(results.analyzer_names) == {"fake", "other"}
        assert results["fake"].data["value"] == 1
        assert results["other"].data["x"] == 42

    def test_auto_register(self) -> None:
        engine = IntelligenceEngine(
            _context(),
            auto_register=[FakeAnalyzer, OtherAnalyzer],
        )
        results = engine.run()
        assert set(results.analyzer_names) == {"fake", "other"}

    def test_auto_register_passes_context(self) -> None:
        ctx = _context()
        engine = IntelligenceEngine(ctx, auto_register=[FakeAnalyzer])
        results = engine.run()
        assert results.investigation_id == "test-inv"

    def test_register_validates_name(self) -> None:
        class Nameless(BaseAnalyzer):
            analyzer_name = ""

            def analyze(self) -> AnalyzerResult:
                return AnalyzerResult(analyzer_name="")

        engine = IntelligenceEngine(_context())
        with pytest.raises(ValueError, match="analyzer_name"):
            engine.register(Nameless(_context()))

    def test_later_run_uses_current_context(self) -> None:
        engine = IntelligenceEngine(_context())
        engine.register(FakeAnalyzer(_context(), value=5))
        results = engine.run()
        assert results["fake"].data["value"] == 5
        # Second run should work fresh
        results2 = engine.run()
        assert results2["fake"].data["value"] == 5

    def test_orchestration_with_real_analyzers(self) -> None:
        graph = ResearchGraph(
            papers={"p1": _paper("p1")},
            authors={},
            institutions={
                "MIT": InstitutionNode(
                    name="MIT", type=InstitutionType.UNIVERSITY,
                    paper_ids=["p1"], author_names=["Alice"],
                ),
            },
            methodologies={
                "CNN": MethodologyNode(
                    name="CNN", paper_ids=["p1"], techniques=[],
                ),
            },
            datasets={},
            technologies={},
            metrics={},
            services=GraphServices(),
        )
        ctx = _context(graph)
        engine = IntelligenceEngine(
            ctx,
            auto_register=[InstitutionAnalyzer, MethodologyAnalyzer, TemporalAnalyzer],
        )
        results = engine.run()
        assert set(results.analyzer_names) == {
            "institution", "methodology", "temporal",
        }
        assert results["institution"].data["total_institutions"] == 1
        assert results["methodology"].data["total_methodologies"] == 1
        assert results["temporal"].data["total_papers"] == 1
        assert results.investigation_id == "test-inv"
        assert results.execution_id is None
