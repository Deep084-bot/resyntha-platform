from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.intelligence.graph.models import ResearchGraph


class CentralityService:
    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def degree_centrality(self, entity_type: str) -> dict[str, float]:
        if entity_type == "author":
            edges = self.co_authorship_edges()
            degrees: dict[str, int] = {}
            for a, b, w in edges:
                degrees[a] = degrees.get(a, 0) + w
                degrees[b] = degrees.get(b, 0) + w
        elif entity_type == "institution":
            edges = self.collaboration_edges()
            degrees = {}
            for a, b, w in edges:
                degrees[a] = degrees.get(a, 0) + w
                degrees[b] = degrees.get(b, 0) + w
        else:
            mapping = {
                "paper": "papers",
                "methodology": "methodologies",
                "dataset": "datasets",
                "technology": "technologies",
                "metric": "metrics",
            }
            entity_dict = getattr(self._graph, mapping.get(entity_type, ""), {})
            degrees = {name: len(node.paper_ids) for name, node in entity_dict.items()}

        max_deg = max(degrees.values()) if degrees else 1
        return {name: d / max_deg for name, d in degrees.items()}

    def co_authorship_edges(self) -> list[tuple[str, str, int]]:
        edge_counts: dict[tuple[str, str], int] = {}
        for paper in self._graph.papers.values():
            names = sorted(a.name for a in paper.authors)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    key = (names[i], names[j])
                    edge_counts[key] = edge_counts.get(key, 0) + 1
        return [(a, b, w) for (a, b), w in edge_counts.items()]

    def collaboration_edges(self) -> list[tuple[str, str, int]]:
        edge_counts: dict[tuple[str, str], int] = {}
        for paper in self._graph.papers.values():
            names = sorted(i.name for i in paper.institutions)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    key = (names[i], names[j])
                    edge_counts[key] = edge_counts.get(key, 0) + 1
        return [(a, b, w) for (a, b), w in edge_counts.items()]
