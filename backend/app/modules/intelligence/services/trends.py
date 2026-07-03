from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.intelligence.graph.models import ResearchGraph

ENTITY_ATTR: dict[str, str] = {
    "paper": "papers",
    "author": "authors",
    "institution": "institutions",
    "methodology": "methodologies",
    "dataset": "datasets",
    "technology": "technologies",
    "metric": "metrics",
}


class TrendService:
    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def _entity_dict(self, entity_type: str) -> dict:
        return getattr(self._graph, ENTITY_ATTR[entity_type])

    def _get_node(self, entity_type: str, name: str):
        return self._entity_dict(entity_type).get(name)

    def year_over_year(
        self,
        entity_type: str,
        name: str,
    ) -> dict[int, int]:
        node = self._get_node(entity_type, name)
        if not node:
            return {}

        counts: dict[int, int] = {}
        for pid in node.paper_ids:
            paper = self._graph.papers.get(pid)
            if paper and paper.year is not None:
                counts[paper.year] = counts.get(paper.year, 0) + 1
        return dict(sorted(counts.items()))

    def first_year(self, entity_type: str, name: str) -> int | None:
        yoy = self.year_over_year(entity_type, name)
        return min(yoy) if yoy else None

    def growth_rate(self, entity_type: str, name: str) -> float:
        yoy = self.year_over_year(entity_type, name)
        if len(yoy) < 2:
            return 0.0

        years = list(yoy.keys())
        prev = yoy[years[-2]]
        curr = yoy[years[-1]]
        if prev == 0:
            return float(curr) if curr else 0.0
        return (curr - prev) / prev

    def is_emerging(self, entity_type: str, name: str, recent_years: int = 3) -> bool:
        yoy = self.year_over_year(entity_type, name)
        if not yoy:
            return False

        graph_years = self._graph.years
        if not graph_years:
            return False

        cutoff = max(graph_years) - recent_years + 1
        max_year = max(yoy)
        return max_year >= cutoff and self.growth_rate(entity_type, name) > 0

    def is_declining(self, entity_type: str, name: str, recent_years: int = 3) -> bool:
        yoy = self.year_over_year(entity_type, name)
        if len(yoy) < 2:
            return False

        return self.growth_rate(entity_type, name) < 0

    def top_emerging(
        self,
        entity_type: str,
        n: int = 10,
        recent_years: int = 3,
    ) -> list[tuple[str, float]]:
        entity_dict = self._entity_dict(entity_type)
        results: list[tuple[str, float]] = []

        for name in entity_dict:
            if self.is_emerging(entity_type, name, recent_years):
                results.append((name, self.growth_rate(entity_type, name)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n]
