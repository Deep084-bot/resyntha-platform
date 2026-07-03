"""Tests for the Intelligence API layer — IntelligenceService + LandscapeResponse."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.modules.intelligence.aggregation import (
    CollaborationSection,
    DatasetSection,
    DiversityMetrics,
    InstitutionEntry,
    InstitutionSection,
    LandscapeAggregator,
    LandscapeResult,
    MethodologyEntry,
    MethodologySection,
    NetworkSection,
    Observation,
    OverviewSection,
    TechnologySection,
    TemporalSection,
)
from app.modules.intelligence.analyzers.models import AnalysisResults, AnalyzerResult
from app.modules.intelligence.api import IntelligenceService, LandscapeResponse
from app.modules.intelligence.api.serializers import landscape_to_response
from app.modules.intelligence.presentation import JsonRenderer, MarkdownRenderer


# =============================================================================
# Helpers — build AnalysisResults without running real analyzers
# =============================================================================


def _result(analyzer_name: str, data: dict[str, Any]) -> AnalyzerResult:
    return AnalyzerResult(analyzer_name=analyzer_name, data=data)


def _results(**kwargs: dict[str, Any]) -> AnalysisResults:
    return AnalysisResults(
        results={name: _result(name, data) for name, data in kwargs.items()},
    )


def _full_analysis_results() -> AnalysisResults:
    return _results(
        institution={
            "total_institutions": 2,
            "institution_type_distribution": {"university": 1, "company": 1},
            "top_institutions": [
                {"name": "MIT", "type": "university", "paper_count": 10, "author_count": 5},
                {"name": "Google", "type": "company", "paper_count": 3, "author_count": 2},
            ],
        },
        methodology={
            "total_methodologies": 2,
            "methodologies": [
                {"name": "CNN", "paper_count": 8, "technique_count": 2, "techniques": ["conv", "pool"]},
                {"name": "RNN", "paper_count": 3, "technique_count": 1, "techniques": ["backprop"]},
            ],
        },
        temporal={
            "total_papers": 10,
            "years_covered": [2022, 2023, 2024],
            "papers_per_year": {2022: 4, 2023: 3, 2024: 3},
        },
        technology={
            "total_technologies": 2,
            "top_technologies": [("PyTorch", 5), ("JAX", 3)],
            "first_appearance_by_year": {"PyTorch": 2022, "JAX": 2024},
            "diversity": {"total_technologies": 2, "papers_with_technology": 8, "avg_papers_per_technology": 4.0},
        },
        dataset={
            "total_datasets": 2,
            "top_datasets": [("ImageNet", 4), ("COCO", 3)],
            "diversity": {"total_datasets": 2, "papers_with_dataset": 7, "avg_papers_per_dataset": 3.5},
        },
        collaboration={
            "institution_network": {
                "total_institutions": 3,
                "total_collaborations": 2,
                "degree_centrality": {"MIT": 0.8},
                "top_by_centrality": [("MIT", 0.8)],
            },
            "author_network": {
                "total_authors": 4,
                "total_collaborations": 3,
                "degree_centrality": {"Alice": 0.9},
                "top_by_centrality": [("Alice", 0.9)],
            },
            "institution_collaborations": [("MIT", "Stanford", 2)],
            "author_collaborations": [("Alice", "Bob", 3)],
        },
    )


@dataclass
class SpyRenderer:
    """Renderer that records the landscape it receives for verification."""

    received: list[LandscapeResult] = field(default_factory=list)
    return_value: str | dict = ""

    def render(self, landscape: LandscapeResult) -> Any:
        self.received.append(landscape)
        return self.return_value


# =============================================================================
# IntelligenceService — construction
# =============================================================================


class TestServiceConstruction:
    def test_default_construction(self) -> None:
        svc = IntelligenceService()
        assert svc is not None

    def test_dependency_injection(self) -> None:
        svc = IntelligenceService(
            aggregator=LandscapeAggregator(),
            markdown_renderer=MarkdownRenderer(),
            json_renderer=JsonRenderer(),
        )
        assert svc is not None


# =============================================================================
# IntelligenceService — get_landscape
# =============================================================================


class TestServiceGetLandscape:
    def test_empty_results_returns_empty_response(self) -> None:
        svc = IntelligenceService()
        result = svc.get_landscape(_results())
        assert isinstance(result, LandscapeResponse)
        assert result.overview.total_papers == 0
        assert result.institutions.total == 0
        assert result.methodologies.total == 0
        assert result.technologies.total == 0
        assert result.datasets.total == 0
        assert result.temporal.total_papers == 0
        assert result.collaborations.institution_network.total_nodes == 0
        assert result.observations == []

    def test_partial_institution_only(self) -> None:
        svc = IntelligenceService()
        result = svc.get_landscape(_results(
            institution={
                "total_institutions": 1,
                "top_institutions": [
                    {"name": "MIT", "type": "university", "paper_count": 5, "author_count": 3},
                ],
                "institution_type_distribution": {"university": 1},
            },
        ))
        assert isinstance(result, LandscapeResponse)
        assert result.institutions.total == 1
        assert len(result.institutions.top_institutions) == 1
        assert result.institutions.top_institutions[0].name == "MIT"
        # Other sections should be empty/default
        assert result.methodologies.total == 0
        assert result.technologies.total == 0

    def test_full_results_return_landscape_response(self) -> None:
        svc = IntelligenceService()
        result = svc.get_landscape(_full_analysis_results())
        assert isinstance(result, LandscapeResponse)
        assert result.overview.total_papers == 10
        assert result.institutions.total == 2
        assert result.methodologies.total == 2
        assert result.technologies.total == 2
        assert result.datasets.total == 2
        assert len(result.temporal.papers_per_year) == 3
        assert result.collaborations.institution_network.total_nodes == 3
        assert len(result.observations) > 0
        # Verify the statistics section is NOT in the response
        assert not hasattr(result, "statistics")

    def test_invalid_results_raises_error(self) -> None:
        svc = IntelligenceService()
        with pytest.raises((TypeError, AttributeError)):
            svc.get_landscape(None)  # type: ignore[arg-type]

    def test_deterministic_output(self) -> None:
        svc = IntelligenceService()
        results = _full_analysis_results()
        r1 = svc.get_landscape(results)
        r2 = svc.get_landscape(results)
        # Compare field-by-field since dataclass equality is value-based
        assert r1 == r2

    def test_observations_are_in_response(self) -> None:
        svc = IntelligenceService()
        result = svc.get_landscape(_full_analysis_results())
        assert len(result.observations) > 0
        obs_labels = {o.label for o in result.observations}
        assert "Most active institution" in obs_labels
        assert "Most common methodology" in obs_labels

    def test_overview_summary_is_correct(self) -> None:
        svc = IntelligenceService()
        result = svc.get_landscape(_full_analysis_results())
        o = result.overview
        assert o.total_papers == 10
        assert o.years_covered == [2022, 2023, 2024]
        assert o.total_institutions == 2
        assert o.total_methodologies == 2
        assert o.total_technologies == 2
        assert o.total_datasets == 2
        assert o.total_authors == 4


# =============================================================================
# IntelligenceService — get_markdown
# =============================================================================


class TestServiceGetMarkdown:
    def test_empty_results_returns_string(self) -> None:
        svc = IntelligenceService()
        result = svc.get_markdown(_results())
        assert isinstance(result, str)

    def test_full_results_returns_markdown(self) -> None:
        svc = IntelligenceService()
        result = svc.get_markdown(_full_analysis_results())
        assert isinstance(result, str)
        assert result.startswith("# Research Landscape")
        assert "# Research Landscape" in result
        assert "## Overview" in result
        assert "## Institutions" in result
        assert "## Methodologies" in result
        assert "## Technologies" in result
        assert "## Datasets" in result
        assert "## Temporal Trends" in result
        assert "## Collaborations" in result
        assert "## Key Observations" in result

    def test_deterministic_markdown(self) -> None:
        svc = IntelligenceService()
        results = _full_analysis_results()
        r1 = svc.get_markdown(results)
        r2 = svc.get_markdown(results)
        assert r1 == r2


# =============================================================================
# IntelligenceService — get_json
# =============================================================================


class TestServiceGetJson:
    def test_empty_results_returns_dict(self) -> None:
        svc = IntelligenceService()
        result = svc.get_json(_results())
        assert isinstance(result, dict)

    def test_full_results_returns_dict(self) -> None:
        svc = IntelligenceService()
        result = svc.get_json(_full_analysis_results())
        assert isinstance(result, dict)
        assert "overview" in result
        assert "institutions" in result
        assert "methodologies" in result
        assert "technologies" in result
        assert "datasets" in result
        assert "temporal" in result
        assert "collaborations" in result
        assert "observations" in result

    def test_deterministic_json(self) -> None:
        svc = IntelligenceService()
        results = _full_analysis_results()
        r1 = svc.get_json(results)
        r2 = svc.get_json(results)
        assert r1 == r2

    def test_json_no_statistics_section(self) -> None:
        """JSON output should not contain an internal-only statistics key."""
        svc = IntelligenceService()
        result = svc.get_json(_full_analysis_results())
        assert "statistics" not in result


# =============================================================================
# IntelligenceService — uses real Aggregator but allows renderer injection
# =============================================================================


class TestServiceRendererInjection:
    def test_custom_renderers_are_used(self) -> None:
        md_spy = SpyRenderer()
        md_spy.return_value = "custom markdown"
        js_spy = SpyRenderer()
        js_spy.return_value = {"custom": True}

        svc = IntelligenceService(
            markdown_renderer=md_spy,  # type: ignore[arg-type]
            json_renderer=js_spy,  # type: ignore[arg-type]
        )
        results = _full_analysis_results()

        md_result = svc.get_markdown(results)
        assert md_result == "custom markdown"
        assert len(md_spy.received) == 1

        js_result = svc.get_json(results)
        assert js_result == {"custom": True}
        assert len(js_spy.received) == 1

    def test_real_renderers_produce_different_outputs(self) -> None:
        svc = IntelligenceService()
        results = _full_analysis_results()
        md = svc.get_markdown(results)
        js = svc.get_json(results)
        assert isinstance(md, str)
        assert isinstance(js, dict)
        assert len(md) != len(str(js))  # different formats


# =============================================================================
# Serializer
# =============================================================================


class TestSerializer:
    def test_landscape_to_response_excludes_statistics(self) -> None:
        landscape = LandscapeResult(
            overview=OverviewSection(total_papers=5),
            statistics=object(),  # anything — should be stripped
        )
        response = landscape_to_response(landscape)
        assert isinstance(response, LandscapeResponse)
        assert not hasattr(response, "statistics")
        assert response.overview.total_papers == 5

    def test_landscape_to_response_preserves_observations(self) -> None:
        obs = [Observation(category="test", label="X", value="1")]
        landscape = LandscapeResult(
            observations=obs,
            overview=OverviewSection(total_papers=1),
        )
        response = landscape_to_response(landscape)
        assert response.observations == obs
        assert len(response.observations) == 1


# =============================================================================
# LandscapeResponse model
# =============================================================================


class TestLandscapeResponseModel:
    def test_default_construction(self) -> None:
        response = LandscapeResponse()
        assert response.overview.total_papers == 0
        assert response.institutions.total == 0
        assert response.methodologies.total == 0
        assert response.technologies.total == 0
        assert response.datasets.total == 0
        assert response.temporal.total_papers == 0
        assert response.collaborations.institution_network.total_nodes == 0
        assert response.observations == []

    def test_custom_construction(self) -> None:
        overview = OverviewSection(total_papers=42)
        response = LandscapeResponse(overview=overview)
        assert response.overview.total_papers == 42

    def test_is_dataclass(self) -> None:
        import dataclasses
        assert dataclasses.is_dataclass(LandscapeResponse)

    def test_has_no_statistics_field(self) -> None:
        """LandscapeResponse must not leak the internal statistics section."""
        assert not hasattr(LandscapeResponse, "statistics")

    def test_response_is_deterministic(self) -> None:
        r1 = LandscapeResponse(
            overview=OverviewSection(total_papers=10),
            observations=[Observation(category="a", label="b", value="c")],
        )
        r2 = LandscapeResponse(
            overview=OverviewSection(total_papers=10),
            observations=[Observation(category="a", label="b", value="c")],
        )
        assert r1 == r2
