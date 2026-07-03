from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

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


class CoOccurrenceService:
    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def _entity_dict(self, entity_type: str) -> dict:
        return getattr(self._graph, ENTITY_ATTR[entity_type])

    def _get_node(self, entity_type: str, name: str):
        return self._entity_dict(entity_type).get(name)

    def between(
        self,
        entity_a_type: str,
        name_a: str,
        entity_b_type: str,
        name_b: str,
    ) -> int:
        node_a = self._get_node(entity_a_type, name_a)
        node_b = self._get_node(entity_b_type, name_b)
        if not node_a or not node_b:
            return 0
        return len(set(node_a.paper_ids) & set(node_b.paper_ids))

    def matrix(
        self,
        entity_type: str,
        names: Sequence[str] | None = None,
    ) -> dict[str, dict[str, int]]:
        entity_dict = self._entity_dict(entity_type)
        target_names = names or list(entity_dict.keys())

        result: dict[str, dict[str, int]] = {}
        for name_a in target_names:
            node_a = entity_dict.get(name_a)
            if not node_a:
                result[name_a] = {}
                continue
            papers_a = set(node_a.paper_ids)
            row: dict[str, int] = {}
            for name_b in target_names:
                if name_a == name_b:
                    continue
                node_b = entity_dict.get(name_b)
                if node_b:
                    count = len(papers_a & set(node_b.paper_ids))
                    if count:
                        row[name_b] = count
            result[name_a] = row
        return result

    def top_co_occurring(
        self,
        entity_type: str,
        name: str,
        n: int = 10,
    ) -> list[tuple[str, int]]:
        entity_dict = self._entity_dict(entity_type)
        node = entity_dict.get(name)
        if not node:
            return []

        papers_a = set(node.paper_ids)
        results: list[tuple[str, int]] = []
        for other_name, other_node in entity_dict.items():
            if other_name == name:
                continue
            count = len(papers_a & set(other_node.paper_ids))
            if count:
                results.append((other_name, count))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n]
