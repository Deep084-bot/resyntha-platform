from __future__ import annotations

import math
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


class StatisticsService:
    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def _entity_dict(self, entity_type: str) -> dict:
        return getattr(self._graph, ENTITY_ATTR[entity_type])

    def frequency_distribution(
        self,
        entity_type: str,
        normalize: bool = True,
    ) -> dict[str, int | float]:
        entity_dict = self._entity_dict(entity_type)
        result: dict[str, int] = {}
        for name, node in entity_dict.items():
            result[name] = len(node.paper_ids)

        if normalize:
            total = sum(result.values()) or 1
            return {k: v / total for k, v in result.items()}
        return result

    def top_n(self, entity_type: str, n: int = 10) -> list[tuple[str, int]]:
        raw = self.frequency_distribution(entity_type, normalize=False)
        sorted_items = sorted(raw.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:n]

    def z_scores(self, values: Sequence[float]) -> list[float]:
        n = len(values)
        if n == 0:
            return []
        if n == 1:
            return [0.0]

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = math.sqrt(variance) if variance else 1.0
        return [(v - mean) / std for v in values]

    def percentile(self, values: Sequence[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (p / 100.0) * (len(sorted_vals) - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)
