from __future__ import annotations

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class DatasetAnalyzer(BaseAnalyzer):
    analyzer_name = "dataset"

    def analyze(self) -> AnalyzerResult:
        graph = self.graph
        config = self.config
        services = graph.services
        max_results = config.max_results_per_analyzer
        co_occurrence = services.co_occurrence
        trends = services.trends
        statistics = services.statistics

        datasets = graph.datasets
        if not datasets:
            return AnalyzerResult(
                analyzer_name=self.analyzer_name,
                data={
                    "popularity": {},
                    "popularity_ranking": [],
                    "diversity": {
                        "total_datasets": 0,
                        "papers_with_dataset": 0,
                        "avg_papers_per_dataset": 0.0,
                    },
                    "yearly_usage_trends": {},
                    "methodology_relationships": {},
                    "technology_relationships": {},
                    "top_datasets": [],
                },
            )

        raw_freq = statistics.frequency_distribution("dataset", normalize=False)
        ranking = statistics.top_n("dataset", n=max_results)

        yearly_trends: dict[str, dict[int, int]] = {}
        for dname in datasets:
            yearly_trends[dname] = trends.year_over_year("dataset", dname)

        methodology_relationships: dict[str, list[tuple[str, int]]] = {}
        for dname in datasets:
            pairs: list[tuple[str, int]] = []
            for mname in graph.methodologies:
                count = co_occurrence.between(
                    "dataset", dname, "methodology", mname,
                )
                if count:
                    pairs.append((mname, count))
            pairs.sort(key=lambda x: x[1], reverse=True)
            methodology_relationships[dname] = pairs[:max_results]

        technology_relationships: dict[str, list[tuple[str, int]]] = {}
        for dname in datasets:
            pairs: list[tuple[str, int]] = []
            for tname in graph.technologies:
                count = co_occurrence.between(
                    "dataset", dname, "technology", tname,
                )
                if count:
                    pairs.append((tname, count))
            pairs.sort(key=lambda x: x[1], reverse=True)
            technology_relationships[dname] = pairs[:max_results]

        paper_ids_with_dataset: set[str] = set()
        for dnode in datasets.values():
            paper_ids_with_dataset.update(dnode.paper_ids)
        ds_count = len(datasets) or 1

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "popularity": raw_freq,
                "popularity_ranking": ranking,
                "diversity": {
                    "total_datasets": len(datasets),
                    "papers_with_dataset": len(paper_ids_with_dataset),
                    "avg_papers_per_dataset": round(
                        sum(len(d.paper_ids) for d in datasets.values())
                        / ds_count,
                        2,
                    ),
                },
                "yearly_usage_trends": yearly_trends,
                "methodology_relationships": methodology_relationships,
                "technology_relationships": technology_relationships,
                "top_datasets": ranking,
            },
        )
