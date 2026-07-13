from __future__ import annotations

from typing import Any

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class TemporalAnalyzer(BaseAnalyzer):
    analyzer_name = "temporal"

    def analyze(self) -> AnalyzerResult:
        graph = self.graph

        papers_per_year: dict[int, int] = {}
        for paper in graph.papers.values():
            if paper.year is not None:
                papers_per_year[paper.year] = papers_per_year.get(paper.year, 0) + 1

        methodology_trends: dict[str, dict[int, int]] = {}
        for mname, mnode in graph.methodologies.items():
            per_year: dict[int, int] = {}
            for pid in mnode.paper_ids:
                paper = graph.papers.get(pid)
                if paper and paper.year is not None:
                    per_year[paper.year] = per_year.get(paper.year, 0) + 1
            if per_year:
                methodology_trends[mname] = per_year

        institution_trends: dict[str, dict[int, int]] = {}
        for iname, inode in graph.institutions.items():
            per_year: dict[int, int] = {}
            for pid in inode.paper_ids:
                paper = graph.papers.get(pid)
                if paper and paper.year is not None:
                    per_year[paper.year] = per_year.get(paper.year, 0) + 1
            if per_year:
                institution_trends[iname] = per_year

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "years_covered": sorted(papers_per_year.keys()),
                "total_papers": graph.paper_count,
                "papers_per_year": dict(sorted(papers_per_year.items())),
                "methodology_trends": methodology_trends,
                "institution_trends": institution_trends,
            }
            | {
                k: v
                for k, v in {
                    "technology_trends": self._compute_entity_trends(graph.technologies),
                    "dataset_trends": self._compute_entity_trends(graph.datasets),
                }.items()
                if v
            },
        )

    def _compute_entity_trends(
        self,
        entities: dict[str, Any],
    ) -> dict[str, dict[int, int]]:
        trends: dict[str, dict[int, int]] = {}
        for ename, enode in entities.items():
            per_year: dict[int, int] = {}
            for pid in enode.paper_ids:
                paper = self.graph.papers.get(pid)
                if paper and paper.year is not None:
                    per_year[paper.year] = per_year.get(paper.year, 0) + 1
            if per_year:
                trends[ename] = per_year
        return trends
