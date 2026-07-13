"""Unit tests for the aggregation layer (Sprint 2.4).

Covers:
  - LandscapeAggregator with empty/partial/complete/malformed data
  - LandscapeResult section models
  - Deterministic observations
  - Missing analyzer handling
"""

from __future__ import annotations

from app.modules.intelligence import (
    AnalysisResults,
    AnalyzerResult,
    LandscapeAggregator,
    LandscapeResult,
    MethodologyEntry,
    NetworkSection,
)

# ======================================================================
# Helpers — build fake AnalyzerResult matching real analyzer shapes
# ======================================================================

_INSTITUTION = AnalyzerResult(
    analyzer_name="institution",
    data={
        "total_institutions": 3,
        "institution_type_distribution": {"university": 2, "company": 1},
        "top_institutions": [
            {"name": "MIT", "type": "university", "paper_count": 10, "author_count": 5},
            {"name": "Stanford", "type": "university", "paper_count": 7, "author_count": 4},
            {"name": "Google", "type": "company", "paper_count": 3, "author_count": 2},
        ],
        "institutions_by_type": {
            "university": [
                {"name": "MIT", "type": "university", "paper_count": 10, "author_count": 5},
                {"name": "Stanford", "type": "university", "paper_count": 7, "author_count": 4},
            ],
            "company": [
                {"name": "Google", "type": "company", "paper_count": 3, "author_count": 2},
            ],
        },
    },
)

_METHODOLOGY = AnalyzerResult(
    analyzer_name="methodology",
    data={
        "total_methodologies": 2,
        "methodologies": [
            {
                "name": "CNN",
                "paper_count": 15,
                "technique_count": 2,
                "techniques": ["convolution", "pooling"],
            },
            {
                "name": "RNN",
                "paper_count": 8,
                "technique_count": 1,
                "techniques": ["backpropagation"],
            },
        ],
    },
)

_TEMPORAL = AnalyzerResult(
    analyzer_name="temporal",
    data={
        "years_covered": [2022, 2023, 2024],
        "total_papers": 25,
        "papers_per_year": {2022: 5, 2023: 10, 2024: 10},
        "methodology_trends": {},
        "institution_trends": {},
    },
)

_TECHNOLOGY = AnalyzerResult(
    analyzer_name="technology",
    data={
        "frequency": {"PyTorch": 12, "TensorFlow": 8, "JAX": 3},
        "popularity_ranking": [("PyTorch", 12), ("TensorFlow", 8), ("JAX", 3)],
        "first_appearance_by_year": {"PyTorch": 2022, "TensorFlow": 2023, "JAX": 2024},
        "yearly_adoption_timeline": {
            "PyTorch": {2022: 4, 2023: 4, 2024: 4},
            "TensorFlow": {2023: 4, 2024: 4},
            "JAX": {2024: 3},
        },
        "methodology_co_occurrence": {},
        "dataset_co_occurrence": {},
        "top_technologies": [("PyTorch", 12), ("TensorFlow", 8), ("JAX", 3)],
        "diversity": {
            "total_technologies": 3,
            "papers_with_technology": 20,
            "avg_papers_per_technology": 7.67,
        },
    },
)

_DATASET = AnalyzerResult(
    analyzer_name="dataset",
    data={
        "popularity": {"ImageNet": 15, "COCO": 10, "CIFAR-10": 5},
        "popularity_ranking": [("ImageNet", 15), ("COCO", 10), ("CIFAR-10", 5)],
        "diversity": {
            "total_datasets": 3,
            "papers_with_dataset": 22,
            "avg_papers_per_dataset": 10.0,
        },
        "yearly_usage_trends": {},
        "methodology_relationships": {},
        "technology_relationships": {},
        "top_datasets": [("ImageNet", 15), ("COCO", 10), ("CIFAR-10", 5)],
    },
)

_COLLABORATION = AnalyzerResult(
    analyzer_name="collaboration",
    data={
        "institution_collaborations": [("MIT", "Stanford", 3), ("MIT", "Google", 1)],
        "author_collaborations": [("Alice", "Bob", 5)],
        "institution_network": {
            "total_institutions": 3,
            "total_collaborations": 2,
            "degree_centrality": {"MIT": 1.0, "Stanford": 0.67, "Google": 0.33},
            "top_by_centrality": [("MIT", 1.0), ("Stanford", 0.67)],
        },
        "author_network": {
            "total_authors": 5,
            "total_collaborations": 3,
            "degree_centrality": {"Alice": 1.0, "Bob": 0.8, "Charlie": 0.5},
            "top_by_centrality": [("Alice", 1.0), ("Bob", 0.8)],
        },
    },
)


def _results(**overrides: AnalyzerResult) -> AnalysisResults:
    defaults: dict[str, AnalyzerResult] = {}
    defaults.update(overrides)
    return AnalysisResults(
        results=defaults,
        investigation_id="test-inv",
        execution_id=None,
    )


# ======================================================================
# LandscapeAggregator — empty / partial / complete
# ======================================================================


class TestLandscapeAggregator:
    def test_empty_results(self) -> None:
        results = _results()
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)
        assert isinstance(landscape, LandscapeResult)
        assert landscape.overview.total_papers == 0
        assert landscape.overview.years_covered == []
        assert landscape.institutions.total == 0
        assert landscape.methodologies.total == 0
        assert landscape.technologies.total == 0
        assert landscape.datasets.total == 0
        assert landscape.collaborations.institution_network.total_nodes == 0
        assert landscape.collaborations.author_network.total_nodes == 0
        assert landscape.statistics.total_papers == 0
        assert landscape.observations == []

    def test_partial_institution_only(self) -> None:
        results = _results(institution=_INSTITUTION)
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)

        assert landscape.institutions.total == 3
        assert len(landscape.institutions.top_institutions) == 3
        assert landscape.institutions.top_institutions[0].name == "MIT"
        assert landscape.institutions.top_institutions[0].paper_count == 10

        assert landscape.methodologies.total == 0
        assert landscape.technologies.total == 0
        assert landscape.datasets.total == 0
        assert landscape.overview.total_papers == 0

    def test_partial_methodology_and_temporal(self) -> None:
        results = _results(methodology=_METHODOLOGY, temporal=_TEMPORAL)
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)

        assert landscape.methodologies.total == 2
        assert landscape.methodologies.top_methodologies[0].name == "CNN"
        assert landscape.methodologies.top_methodologies[0].technique_count == 2
        assert landscape.temporal.total_papers == 25
        assert landscape.temporal.years_covered == [2022, 2023, 2024]
        assert landscape.overview.total_papers == 25

    def test_complete_all_analyzers(self) -> None:
        results = _results(
            institution=_INSTITUTION,
            methodology=_METHODOLOGY,
            temporal=_TEMPORAL,
            technology=_TECHNOLOGY,
            dataset=_DATASET,
            collaboration=_COLLABORATION,
        )
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)

        # Overview
        assert landscape.overview.total_papers == 25
        assert landscape.overview.years_covered == [2022, 2023, 2024]
        assert landscape.overview.total_institutions == 3
        assert landscape.overview.total_methodologies == 2
        assert landscape.overview.total_technologies == 3
        assert landscape.overview.total_datasets == 3
        assert landscape.overview.total_authors == 5

        # Institutions
        assert landscape.institutions.type_distribution["university"] == 2
        assert landscape.institutions.type_distribution["company"] == 1
        assert "university" in landscape.institutions.institutions_by_type
        assert len(landscape.institutions.institutions_by_type["university"]) == 2

        # Methodologies
        assert isinstance(landscape.methodologies.top_methodologies[0], MethodologyEntry)
        assert landscape.methodologies.top_methodologies[0].techniques == ["convolution", "pooling"]

        # Technologies
        assert landscape.technologies.top_technologies[0] == ("PyTorch", 12)
        assert landscape.technologies.first_appearance_by_year["JAX"] == 2024
        assert landscape.technologies.diversity.total == 3
        assert landscape.technologies.diversity.papers_with_entity == 20
        assert landscape.technologies.diversity.avg_papers_per_entity == 7.67

        # Datasets
        assert landscape.datasets.top_datasets[0] == ("ImageNet", 15)
        assert landscape.datasets.diversity.total == 3
        assert landscape.datasets.yearly_usage_trends == {}

        # Temporal
        assert landscape.temporal.papers_per_year[2022] == 5
        assert landscape.temporal.papers_per_year[2023] == 10

        # Collaborations
        assert landscape.collaborations.top_institution_collaborations[0] == ("MIT", "Stanford", 3)
        inst_net = landscape.collaborations.institution_network
        assert isinstance(inst_net, NetworkSection)
        assert inst_net.total_nodes == 3
        assert inst_net.total_edges == 2
        assert inst_net.degree_centrality["MIT"] == 1.0

        auth_net = landscape.collaborations.author_network
        assert auth_net.total_nodes == 5
        assert auth_net.top_by_centrality[0] == ("Alice", 1.0)

        # Statistics
        assert landscape.statistics.papers_per_year[2022] == 5
        assert landscape.statistics.total_papers == 25

    def test_malformed_missing_keys(self) -> None:
        results = _results(
            institution=AnalyzerResult(analyzer_name="institution", data={}),
            temporal=AnalyzerResult(analyzer_name="temporal", data={"total_papers": 10}),
        )
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)

        assert landscape.institutions.total == 0
        assert landscape.institutions.top_institutions == []
        assert landscape.temporal.total_papers == 10
        assert landscape.temporal.years_covered == []

    def test_malformed_wrong_types(self) -> None:
        results = _results(
            institution=AnalyzerResult(
                analyzer_name="institution",
                data={
                    "total_institutions": "not_an_int",
                    "top_institutions": "not_a_list",
                },
            ),
        )
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)
        assert landscape.institutions.total == 0
        assert landscape.institutions.top_institutions == []

    def test_missing_optional_temporal_keys(self) -> None:
        results = _results(
            temporal=AnalyzerResult(analyzer_name="temporal", data={}),
        )
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)
        assert landscape.temporal.years_covered == []
        assert landscape.temporal.papers_per_year == {}
        assert landscape.temporal.total_papers == 0

    def test_empty_diversity_metrics(self) -> None:
        results = _results(
            technology=AnalyzerResult(
                analyzer_name="technology",
                data={"diversity": {}},
            ),
            dataset=AnalyzerResult(
                analyzer_name="dataset",
                data={"diversity": {}},
            ),
        )
        agg = LandscapeAggregator()
        landscape = agg.aggregate(results)
        assert landscape.technologies.diversity.total == 0
        assert landscape.technologies.diversity.papers_with_entity == 0
        assert landscape.datasets.diversity.total == 0
        assert landscape.datasets.diversity.papers_with_entity == 0


# ======================================================================
# Observations
# ======================================================================


class TestObservations:
    def test_empty_results_no_observations(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results())
        assert landscape.observations == []

    def test_most_active_institution(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(institution=_INSTITUTION))
        obs = {o.label: o for o in landscape.observations}
        assert "Most active institution" in obs
        assert obs["Most active institution"].value == "MIT (10 papers)"

    def test_most_common_methodology(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(methodology=_METHODOLOGY))
        obs = {o.label: o for o in landscape.observations}
        assert "Most common methodology" in obs
        assert obs["Most common methodology"].value == "CNN (15 papers)"

    def test_most_used_technology(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(technology=_TECHNOLOGY))
        obs = {o.label: o for o in landscape.observations}
        assert "Most used technology" in obs
        assert obs["Most used technology"].value == "PyTorch (12 papers)"

    def test_most_used_dataset(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(dataset=_DATASET))
        obs = {o.label: o for o in landscape.observations}
        assert "Most used dataset" in obs
        assert obs["Most used dataset"].value == "ImageNet (15 papers)"

    def test_research_time_span(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(temporal=_TEMPORAL))
        obs = {o.label: o for o in landscape.observations}
        assert "Research time span" in obs
        assert obs["Research time span"].value == "2022–2024"

    def test_research_time_span_single_year(self) -> None:
        agg = LandscapeAggregator()
        temp = AnalyzerResult(
            analyzer_name="temporal",
            data={
                "years_covered": [2024],
                "total_papers": 5,
                "papers_per_year": {2024: 5},
                "methodology_trends": {},
                "institution_trends": {},
            },
        )
        landscape = agg.aggregate(_results(temporal=temp))
        obs = {o.label: o for o in landscape.observations}
        assert obs["Research time span"].value == "2024"

    def test_total_research_output(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(temporal=_TEMPORAL))
        obs = {o.label: o for o in landscape.observations}
        assert "Total research output" in obs
        assert "25 papers" in obs["Total research output"].value

    def test_methodology_diversity(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(methodology=_METHODOLOGY))
        obs = {o.label: o for o in landscape.observations}
        assert "Methodology diversity" in obs
        assert "2" in obs["Methodology diversity"].value

    def test_institution_collaboration_intensity(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(collaboration=_COLLABORATION))
        obs = {o.label: o for o in landscape.observations}
        assert "Institution collaboration intensity" in obs

    def test_author_collaboration_network(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(collaboration=_COLLABORATION))
        obs = {o.label: o for o in landscape.observations}
        assert "Author collaboration network" in obs

    def test_newest_technology(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(technology=_TECHNOLOGY))
        obs = {o.label: o for o in landscape.observations}
        assert "Newest technology" in obs
        assert obs["Newest technology"].value == "JAX (first appeared 2024)"

    def test_technology_adoption_rate(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(technology=_TECHNOLOGY))
        obs = {o.label: o for o in landscape.observations}
        assert "Technology adoption rate" in obs

    def test_dataset_reuse_rate(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(dataset=_DATASET))
        obs = {o.label: o for o in landscape.observations}
        assert "Dataset reuse rate" in obs

    def test_most_common_institution_type(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(institution=_INSTITUTION))
        obs = {o.label: o for o in landscape.observations}
        assert "Most common institution type" in obs

    def test_observations_are_deterministic(self) -> None:
        agg = LandscapeAggregator()
        results = _results(
            institution=_INSTITUTION,
            methodology=_METHODOLOGY,
            temporal=_TEMPORAL,
            technology=_TECHNOLOGY,
            dataset=_DATASET,
            collaboration=_COLLABORATION,
        )
        landscape_a = agg.aggregate(results)
        landscape_b = agg.aggregate(results)
        labels_a = [(o.category, o.label, o.value) for o in landscape_a.observations]
        labels_b = [(o.category, o.label, o.value) for o in landscape_b.observations]
        assert labels_a == labels_b

    def test_observation_category_labels(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(
            _results(
                institution=_INSTITUTION,
                methodology=_METHODOLOGY,
                temporal=_TEMPORAL,
                technology=_TECHNOLOGY,
                dataset=_DATASET,
                collaboration=_COLLABORATION,
            )
        )
        categories = {o.category for o in landscape.observations}
        assert categories == {
            "institution",
            "methodology",
            "technology",
            "dataset",
            "temporal",
            "collaboration",
        }

    def test_institution_only_observations(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(institution=_INSTITUTION))
        categories = {o.category for o in landscape.observations}
        assert categories == {"institution"}
        assert len(landscape.observations) == 2

    def test_observation_has_typed_fields(self) -> None:
        agg = LandscapeAggregator()
        landscape = agg.aggregate(_results(institution=_INSTITUTION))
        obs = landscape.observations[0]
        assert isinstance(obs.category, str)
        assert isinstance(obs.label, str)
        assert isinstance(obs.value, str)
