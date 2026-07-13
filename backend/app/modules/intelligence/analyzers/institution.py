from __future__ import annotations

from typing import Any

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class InstitutionAnalyzer(BaseAnalyzer):
    analyzer_name = "institution"

    def analyze(self) -> AnalyzerResult:
        institutions = self.graph.institutions
        max_results = self.config.max_results_per_analyzer

        type_dist: dict[str, int] = {}
        institutions_by_type: dict[str, list[dict[str, Any]]] = {}
        top: list[dict[str, Any]] = []

        for name, node in institutions.items():
            t = node.type.value
            type_dist[t] = type_dist.get(t, 0) + 1
            entry: dict[str, Any] = {
                "name": name,
                "type": t,
                "paper_count": len(node.paper_ids),
                "author_count": len(node.author_names),
            }
            top.append(entry)
            institutions_by_type.setdefault(t, []).append(entry)

        top.sort(key=lambda x: x["paper_count"], reverse=True)

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "total_institutions": len(institutions),
                "institution_type_distribution": type_dist,
                "top_institutions": top[:max_results],
                "institutions_by_type": {
                    t: sorted(entries, key=lambda x: x["paper_count"], reverse=True)[:max_results]
                    for t, entries in institutions_by_type.items()
                },
            },
        )
