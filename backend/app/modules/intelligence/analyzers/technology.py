from __future__ import annotations

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class TechnologyAnalyzer(BaseAnalyzer):
    analyzer_name = "technology"

    def analyze(self) -> AnalyzerResult:
        graph = self.graph
        config = self.config
        services = graph.services
        max_results = config.max_results_per_analyzer
        co_occurrence = services.co_occurrence
        trends = services.trends
        statistics = services.statistics

        technologies = graph.technologies
        if not technologies:
            return AnalyzerResult(
                analyzer_name=self.analyzer_name,
                data={
                    "frequency": {},
                    "popularity_ranking": [],
                    "first_appearance_by_year": {},
                    "yearly_adoption_timeline": {},
                    "methodology_co_occurrence": {},
                    "dataset_co_occurrence": {},
                    "top_technologies": [],
                    "diversity": {
                        "total_technologies": 0,
                        "papers_with_technology": 0,
                        "avg_papers_per_technology": 0.0,
                    },
                },
            )

        raw_freq = statistics.frequency_distribution("technology", normalize=False)
        ranking = statistics.top_n("technology", n=max_results)

        first_appearance: dict[str, int | None] = {}
        adoption_timeline: dict[str, dict[int, int]] = {}
        for tname in technologies:
            first_appearance[tname] = trends.first_year("technology", tname)
            adoption_timeline[tname] = trends.year_over_year("technology", tname)

        methodology_co_occurrence: dict[str, list[tuple[str, int]]] = {}
        for tname in technologies:
            pairs: list[tuple[str, int]] = []
            for mname in graph.methodologies:
                count = co_occurrence.between(
                    "technology",
                    tname,
                    "methodology",
                    mname,
                )
                if count:
                    pairs.append((mname, count))
            pairs.sort(key=lambda x: x[1], reverse=True)
            methodology_co_occurrence[tname] = pairs[:max_results]

        dataset_co_occurrence: dict[str, list[tuple[str, int]]] = {}
        for tname in technologies:
            pairs: list[tuple[str, int]] = []
            for dname in graph.datasets:
                count = co_occurrence.between(
                    "technology",
                    tname,
                    "dataset",
                    dname,
                )
                if count:
                    pairs.append((dname, count))
            pairs.sort(key=lambda x: x[1], reverse=True)
            dataset_co_occurrence[tname] = pairs[:max_results]

        paper_ids_with_tech: set[str] = set()
        for tnode in technologies.values():
            paper_ids_with_tech.update(tnode.paper_ids)
        tech_count = len(technologies) or 1

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "frequency": raw_freq,
                "popularity_ranking": ranking,
                "first_appearance_by_year": first_appearance,
                "yearly_adoption_timeline": adoption_timeline,
                "methodology_co_occurrence": methodology_co_occurrence,
                "dataset_co_occurrence": dataset_co_occurrence,
                "top_technologies": ranking,
                "diversity": {
                    "total_technologies": len(technologies),
                    "papers_with_technology": len(paper_ids_with_tech),
                    "avg_papers_per_technology": round(
                        sum(len(t.paper_ids) for t in technologies.values()) / tech_count,
                        2,
                    ),
                },
            },
        )
