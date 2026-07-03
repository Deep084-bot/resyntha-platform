"""Tests for the presentation layer — MarkdownRenderer and JsonRenderer."""

from __future__ import annotations

import pytest

from app.modules.intelligence.aggregation.models import (
    CollaborationSection,
    DatasetSection,
    DiversityMetrics,
    InstitutionEntry,
    InstitutionSection,
    LandscapeResult,
    MethodologyEntry,
    MethodologySection,
    NetworkSection,
    Observation,
    OverviewSection,
    TechnologySection,
    TemporalSection,
)
from app.modules.intelligence.presentation import (
    BaseRenderer,
    JsonRenderer,
    MarkdownRenderer,
)
from app.modules.intelligence.presentation.json import JsonRenderer as JR
from app.modules.intelligence.presentation.markdown import MarkdownRenderer as MR


# =============================================================================
# Helpers
# =============================================================================


def _landscape(**overrides) -> LandscapeResult:
    """Build a LandscapeResult with sensible defaults for each section."""
    defaults = {
        "overview": OverviewSection(total_papers=10, years_covered=[2022, 2023]),
        "institutions": InstitutionSection(),
        "methodologies": MethodologySection(),
        "technologies": TechnologySection(),
        "datasets": DatasetSection(),
        "temporal": TemporalSection(),
        "collaborations": CollaborationSection(),
        "observations": [],
        "statistics": None,
    }
    defaults.update(overrides)
    return LandscapeResult(**defaults)


# =============================================================================
# BaseRenderer
# =============================================================================


class TestBaseRenderer:
    def test_abstract_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseRenderer()  # type: ignore[abstract]

    def test_concrete_subclasses_ok(self) -> None:
        assert issubclass(MarkdownRenderer, BaseRenderer)
        assert issubclass(JsonRenderer, BaseRenderer)

    def test_both_have_render_method(self) -> None:
        assert hasattr(MarkdownRenderer(), "render")
        assert hasattr(JsonRenderer(), "render")


# =============================================================================
# MarkdownRenderer – basic structure
# =============================================================================


class TestMarkdownRendererStructure:
    def test_empty_landscape_returns_only_title(self) -> None:
        landscape = _landscape(overview=OverviewSection())
        result = MR().render(landscape)
        assert result.startswith("# Research Landscape\n")
        assert result.endswith("\n")
        # No sections for empty data
        assert "## Overview" not in result

    def test_minimal_overview_shows_table(self) -> None:
        landscape = _landscape()
        result = MR().render(landscape)
        assert "## Overview" in result
        assert "| Metric | Value |" in result
        assert "Total Papers" in result
        assert "10" in result
        assert "2022–2023" in result

    def test_title_is_h1(self) -> None:
        result = MR().render(_landscape())
        lines = result.strip().split("\n")
        assert lines[0] == "# Research Landscape"

    def test_sections_appear_in_order(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                top_institutions=[
                    InstitutionEntry(name="MIT", type="university", paper_count=5, author_count=3)
                ],
                type_distribution={"university": 1},
            ),
            methodologies=MethodologySection(
                top_methodologies=[
                    MethodologyEntry(name="CNN", paper_count=5, technique_count=2, techniques=["conv"])
                ]
            ),
            technologies=TechnologySection(
                top_technologies=[("PyTorch", 5)],
                first_appearance_by_year={"PyTorch": 2022},
                diversity=DiversityMetrics(total=1, papers_with_entity=5, avg_papers_per_entity=5.0),
            ),
            datasets=DatasetSection(
                top_datasets=[("ImageNet", 3)],
                diversity=DiversityMetrics(total=1, papers_with_entity=3, avg_papers_per_entity=3.0),
            ),
            temporal=TemporalSection(papers_per_year={2022: 4, 2023: 6}),
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=3, total_edges=2, degree_centrality={}, top_by_centrality=[("MIT", 0.8)]
                ),
                top_institution_collaborations=[("MIT", "Stanford", 2)],
            ),
            observations=[
                Observation(category="institution", label="Top Institution", value="MIT (5 papers)")
            ],
        )
        result = MR().render(landscape)
        sections = ["Overview", "Institutions", "Methodologies", "Technologies", "Datasets", "Temporal Trends", "Collaborations", "Key Observations"]
        prev = -1
        for sec in sections:
            idx = result.find(f"## {sec}")
            assert idx != -1, f"Section '{sec}' not found"
            assert idx > prev, f"Section '{sec}' out of order"
            prev = idx


# =============================================================================
# MarkdownRenderer – sections
# =============================================================================


class TestMarkdownRendererSections:
    def test_institutions_table(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                total=2,
                type_distribution={"university": 2},
                top_institutions=[
                    InstitutionEntry(name="MIT", type="university", paper_count=10, author_count=5),
                    InstitutionEntry(name="Stanford", type="university", paper_count=7, author_count=4),
                ],
            )
        )
        result = MR().render(landscape)
        assert "| Institution | Type | Papers | Authors |" in result
        assert "| MIT | university | 10 | 5 |" in result
        assert "| Stanford | university | 7 | 4 |" in result
        assert "### Type Distribution" in result
        assert "| university | 2 |" in result

    def test_institutions_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Institutions" not in result

    def test_methodologies_table(self) -> None:
        landscape = _landscape(
            methodologies=MethodologySection(
                total=1,
                top_methodologies=[
                    MethodologyEntry(name="CNN", paper_count=8, technique_count=2, techniques=["conv", "pool"])
                ],
            )
        )
        result = MR().render(landscape)
        assert "| Methodology | Papers | Techniques |" in result
        assert "| CNN | 8 | conv, pool |" in result

    def test_methodologies_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Methodologies" not in result

    def test_technologies_table_and_diversity(self) -> None:
        landscape = _landscape(
            technologies=TechnologySection(
                total=2,
                top_technologies=[("PyTorch", 5), ("JAX", 3)],
                first_appearance_by_year={"PyTorch": 2022, "JAX": 2024},
                diversity=DiversityMetrics(total=2, papers_with_entity=8, avg_papers_per_entity=4.0),
            )
        )
        result = MR().render(landscape)
        assert "| Technology | Papers | First Appearance |" in result
        assert "| PyTorch | 5 | 2022 |" in result
        assert "| JAX | 3 | 2024 |" in result
        assert "**Diversity:**" in result
        assert "2 technologies" in result

    def test_technologies_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Technologies" not in result

    def test_datasets_table_and_diversity(self) -> None:
        landscape = _landscape(
            datasets=DatasetSection(
                total=2,
                top_datasets=[("ImageNet", 4), ("COCO", 3)],
                diversity=DiversityMetrics(total=2, papers_with_entity=7, avg_papers_per_entity=3.5),
            )
        )
        result = MR().render(landscape)
        assert "| Dataset | Papers |" in result
        assert "| ImageNet | 4 |" in result
        assert "| COCO | 3 |" in result
        assert "**Diversity:**" in result
        assert "2 datasets" in result

    def test_datasets_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Datasets" not in result

    def test_temporal_table(self) -> None:
        landscape = _landscape(
            temporal=TemporalSection(papers_per_year={2022: 4, 2023: 6})
        )
        result = MR().render(landscape)
        assert "| Year | Papers |" in result
        assert "| 2022 | 4 |" in result
        assert "| 2023 | 6 |" in result

    def test_temporal_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Temporal Trends" not in result

    def test_collaborations_networks(self) -> None:
        landscape = _landscape(
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=3,
                    total_edges=2,
                    degree_centrality={"MIT": 0.8, "Stanford": 0.6},
                    top_by_centrality=[("MIT", 0.8)],
                ),
                top_institution_collaborations=[("MIT", "Stanford", 2)],
                author_network=NetworkSection(
                    total_nodes=4,
                    total_edges=3,
                    degree_centrality={"Alice": 0.9, "Bob": 0.7},
                    top_by_centrality=[("Alice", 0.9)],
                ),
                top_author_collaborations=[("Alice", "Bob", 3)],
            )
        )
        result = MR().render(landscape)
        assert "### Institution Network" in result
        assert "**Nodes:** 3" in result
        assert "**Edges:** 2" in result
        assert "**Most Central:** MIT (centrality 0.80)" in result
        assert "| Institution A | Institution B | Papers |" in result
        assert "| MIT | Stanford | 2 |" in result

        assert "### Author Network" in result
        assert "**Nodes:** 4" in result
        assert "**Edges:** 3" in result
        assert "**Most Central:** Alice (centrality 0.90)" in result
        assert "| Author A | Author B | Papers |" in result
        assert "| Alice | Bob | 3 |" in result

    def test_collaborations_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Collaborations" not in result

    def test_observations_list(self) -> None:
        landscape = _landscape(
            observations=[
                Observation(category="institution", label="Top Institution", value="MIT (5 papers)"),
                Observation(category="methodology", label="Common Methodology", value="CNN"),
            ]
        )
        result = MR().render(landscape)
        assert "## Key Observations" in result
        assert "**Top Institution:** MIT (5 papers)" in result
        assert "**Common Methodology:** CNN" in result

    def test_observations_empty_skipped(self) -> None:
        result = MR().render(_landscape())
        assert "## Key Observations" not in result


# =============================================================================
# MarkdownRenderer – edge cases
# =============================================================================


class TestMarkdownRendererEdgeCases:
    def test_empty_text(self) -> None:
        landscape = _landscape(overview=OverviewSection())
        result = MR().render(landscape)
        assert result.strip() == "# Research Landscape"

    def test_key_in_non_empty_overview(self) -> None:
        result = MR().render(_landscape())
        assert "10" in result

    def test_single_year_format(self) -> None:
        landscape = _landscape(overview=OverviewSection(total_papers=5, years_covered=[2024]))
        result = MR().render(landscape)
        assert "2024" in result
        assert "–" not in result

    def test_empty_technique_list(self) -> None:
        landscape = _landscape(
            methodologies=MethodologySection(
                top_methodologies=[
                    MethodologyEntry(name="CNN", paper_count=3, technique_count=0, techniques=[])
                ]
            )
        )
        result = MR().render(landscape)
        assert "| CNN | 3 | — |" in result

    def test_no_first_appearance(self) -> None:
        landscape = _landscape(
            technologies=TechnologySection(
                top_technologies=[("Custom", 1)],
                first_appearance_by_year={},
                diversity=DiversityMetrics(total=0, papers_with_entity=0, avg_papers_per_entity=0.0),
            )
        )
        result = MR().render(landscape)
        assert "| Custom | 1 | — |" in result

    def test_no_collaboration_edges(self) -> None:
        landscape = _landscape(
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=2, total_edges=0, degree_centrality={}, top_by_centrality=[]
                ),
            )
        )
        result = MR().render(landscape)
        assert "### Institution Network" in result
        assert "**Nodes:** 2" in result
        assert "**Edges:** 0" in result
        # no collaboration table since list is empty
        assert "| Institution A | Institution B | Papers |" not in result

    def test_deterministic_output(self) -> None:
        """Same input always produces identical output."""
        landscape = _landscape(
            institutions=InstitutionSection(
                top_institutions=[
                    InstitutionEntry(name="MIT", type="university", paper_count=5, author_count=2),
                ],
                type_distribution={"university": 1},
            ),
            observations=[Observation(category="inst", label="X", value="1")],
        )
        r1 = MR().render(landscape)
        r2 = MR().render(landscape)
        assert r1 == r2


# =============================================================================
# JsonRenderer
# =============================================================================


class TestJsonRendererBasic:
    def test_empty_landscape_returns_empty_dict(self) -> None:
        landscape = _landscape(overview=OverviewSection())
        result = JR().render(landscape)
        assert result == {}

    def test_returns_dict(self) -> None:
        result = JR().render(_landscape())
        assert isinstance(result, dict)

    def test_overview_present(self) -> None:
        result = JR().render(_landscape())
        assert "overview" in result
        assert result["overview"]["total_papers"] == 10
        assert result["overview"]["years_covered"] == [2022, 2023]

    def test_skips_empty_sections(self) -> None:
        result = JR().render(_landscape())
        for key in ("institutions", "methodologies", "technologies", "datasets", "temporal", "collaborations", "observations"):
            assert key not in result, f"Empty section '{key}' should not be in result"


class TestJsonRendererInstitutions:
    def test_full_section(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                total=2,
                type_distribution={"university": 1, "company": 1},
                top_institutions=[
                    InstitutionEntry(name="MIT", type="university", paper_count=10, author_count=5),
                    InstitutionEntry(name="Google", type="company", paper_count=3, author_count=2),
                ],
            )
        )
        result = JR().render(landscape)
        sec = result["institutions"]
        assert sec["total"] == 2
        assert sec["type_distribution"] == {"university": 1, "company": 1}
        assert sec["top_institutions"][0] == {"name": "MIT", "type": "university", "paper_count": 10, "author_count": 5}
        assert sec["top_institutions"][1] == {"name": "Google", "type": "company", "paper_count": 3, "author_count": 2}


class TestJsonRendererMethodologies:
    def test_methodologies_section(self) -> None:
        landscape = _landscape(
            methodologies=MethodologySection(
                total=2,
                top_methodologies=[
                    MethodologyEntry(name="CNN", paper_count=8, technique_count=2, techniques=["conv", "pool"]),
                    MethodologyEntry(name="RNN", paper_count=3, technique_count=1, techniques=["backprop"]),
                ],
            )
        )
        result = JR().render(landscape)
        sec = result["methodologies"]
        assert sec["total"] == 2
        assert len(sec["methodologies"]) == 2
        assert sec["methodologies"][0] == {
            "name": "CNN",
            "paper_count": 8,
            "technique_count": 2,
            "techniques": ["conv", "pool"],
        }


class TestJsonRendererTechnologies:
    def test_technologies_with_diversity(self) -> None:
        landscape = _landscape(
            technologies=TechnologySection(
                total=2,
                top_technologies=[("PyTorch", 5), ("JAX", 3)],
                first_appearance_by_year={"PyTorch": 2022},
                diversity=DiversityMetrics(total=2, papers_with_entity=8, avg_papers_per_entity=4.0),
            )
        )
        result = JR().render(landscape)
        sec = result["technologies"]
        assert sec["total"] == 2
        assert len(sec["top_technologies"]) == 2
        assert sec["first_appearance_by_year"] == {"PyTorch": 2022}
        assert sec["diversity"]["total_technologies"] == 2
        assert sec["diversity"]["avg_papers_per_technology"] == 4.0


class TestJsonRendererDatasets:
    def test_datasets_with_diversity(self) -> None:
        landscape = _landscape(
            datasets=DatasetSection(
                total=2,
                top_datasets=[("ImageNet", 4), ("COCO", 3)],
                diversity=DiversityMetrics(total=2, papers_with_entity=7, avg_papers_per_entity=3.5),
            )
        )
        result = JR().render(landscape)
        sec = result["datasets"]
        assert sec["total"] == 2
        assert len(sec["top_datasets"]) == 2
        assert sec["diversity"]["total_datasets"] == 2
        assert sec["diversity"]["avg_papers_per_dataset"] == 3.5


class TestJsonRendererTemporal:
    def test_temporal_section(self) -> None:
        landscape = _landscape(
            temporal=TemporalSection(
                years_covered=[2022, 2023],
                papers_per_year={2022: 4, 2023: 6},
            )
        )
        result = JR().render(landscape)
        sec = result["temporal"]
        assert sec["papers_per_year"] == {2022: 4, 2023: 6}
        assert sec["total_papers"] == 0
        assert 2022 in sec["years_covered"]


class TestJsonRendererCollaborations:
    def test_full_collaborations(self) -> None:
        landscape = _landscape(
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=3, total_edges=2, degree_centrality={"MIT": 0.8},
                    top_by_centrality=[("MIT", 0.8)],
                ),
                top_institution_collaborations=[("MIT", "Stanford", 2)],
                author_network=NetworkSection(
                    total_nodes=4, total_edges=3, degree_centrality={"Alice": 0.9},
                    top_by_centrality=[("Alice", 0.9)],
                ),
                top_author_collaborations=[("Alice", "Bob", 3)],
            )
        )
        result = JR().render(landscape)
        sec = result["collaborations"]
        assert "institution_network" in sec
        assert "author_network" in sec
        assert sec["institution_network"]["total_nodes"] == 3
        assert sec["author_network"]["total_nodes"] == 4
        assert len(sec["institution_collaborations"]) == 1
        assert sec["institution_collaborations"][0] == {"source": "MIT", "target": "Stanford", "weight": 2}
        assert sec["author_collaborations"][0] == {"source": "Alice", "target": "Bob", "weight": 3}

    def test_centrality_rounded(self) -> None:
        landscape = _landscape(
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=2, total_edges=1, degree_centrality={"MIT": 0.87654},
                    top_by_centrality=[("MIT", 0.87654)],
                ),
            )
        )
        result = JR().render(landscape)
        top = result["collaborations"]["institution_network"]["top_by_centrality"][0]
        assert top["centrality"] == 0.8765

    def test_inst_only_no_auth(self) -> None:
        landscape = _landscape(
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=2, total_edges=1, degree_centrality={}, top_by_centrality=[]
                ),
            )
        )
        result = JR().render(landscape)
        sec = result["collaborations"]
        assert "institution_network" in sec
        assert "author_network" not in sec


class TestJsonRendererObservations:
    def test_observations_list(self) -> None:
        landscape = _landscape(
            observations=[
                Observation(category="institution", label="Top Institution", value="MIT (5 papers)"),
            ]
        )
        result = JR().render(landscape)
        assert len(result["observations"]) == 1
        assert result["observations"][0] == {
            "category": "institution",
            "label": "Top Institution",
            "value": "MIT (5 papers)",
        }


class TestJsonRendererEdgeCases:
    def test_overview_none_fields_skipped(self) -> None:
        """When overview is all zeros/empty, section is omitted."""
        landscape = _landscape(overview=OverviewSection())
        result = JR().render(landscape)
        assert result == {}

    def test_empty_observations_omitted(self) -> None:
        result = JR().render(_landscape())
        assert "observations" not in result

    def test_deterministic_output(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                top_institutions=[InstitutionEntry(name="MIT", type="university", paper_count=5, author_count=2)],
                type_distribution={"university": 1},
            ),
            observations=[Observation(category="inst", label="X", value="1")],
        )
        r1 = JR().render(landscape)
        r2 = JR().render(landscape)
        assert r1 == r2

    def test_non_empty_result(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                top_institutions=[InstitutionEntry(name="MIT", type="university", paper_count=5, author_count=2)],
                type_distribution={"university": 1},
            ),
        )
        result = JR().render(landscape)
        assert len(result) == 2  # overview + institutions
        assert "overview" in result
        assert "institutions" in result


# =============================================================================
# Quick smoke test: render both formats for a realistic landscape
# =============================================================================


class TestRenderSmoke:
    def test_markdown_and_json(self) -> None:
        landscape = _landscape(
            institutions=InstitutionSection(
                top_institutions=[
                    InstitutionEntry(name="MIT", type="university", paper_count=10, author_count=5),
                ],
                type_distribution={"university": 1},
            ),
            methodologies=MethodologySection(
                top_methodologies=[
                    MethodologyEntry(name="CNN", paper_count=8, technique_count=2, techniques=["conv", "pool"]),
                ]
            ),
            technologies=TechnologySection(
                top_technologies=[("PyTorch", 5)],
                first_appearance_by_year={"PyTorch": 2022},
                diversity=DiversityMetrics(total=1, papers_with_entity=5, avg_papers_per_entity=5.0),
            ),
            datasets=DatasetSection(
                top_datasets=[("ImageNet", 3)],
                diversity=DiversityMetrics(total=1, papers_with_entity=3, avg_papers_per_entity=3.0),
            ),
            temporal=TemporalSection(papers_per_year={2022: 4, 2023: 6}),
            collaborations=CollaborationSection(
                institution_network=NetworkSection(
                    total_nodes=3, total_edges=2, degree_centrality={"MIT": 0.8},
                    top_by_centrality=[("MIT", 0.8)],
                ),
                top_institution_collaborations=[("MIT", "Stanford", 2)],
            ),
            observations=[
                Observation(category="institution", label="Top Institution", value="MIT (10 papers)"),
                Observation(category="methodology", label="Common Methodology", value="CNN (8 papers)"),
            ],
        )

        md = MR().render(landscape)
        js = JR().render(landscape)

        assert isinstance(md, str)
        assert isinstance(js, dict)
        assert len(md) > 200
        assert len(js) >= 5
        assert md.startswith("# Research Landscape")
        assert js["overview"]["total_papers"] == 10
