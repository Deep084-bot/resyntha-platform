from __future__ import annotations

from typing import Any

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class MethodologyAnalyzer(BaseAnalyzer):
    analyzer_name = "methodology"

    def analyze(self) -> AnalyzerResult:
        methodologies = self.graph.methodologies
        max_results = self.config.max_results_per_analyzer

        freq: list[dict[str, Any]] = []
        for name, node in methodologies.items():
            freq.append(
                {
                    "name": name,
                    "paper_count": len(node.paper_ids),
                    "technique_count": len(node.techniques),
                    "techniques": node.techniques,
                }
            )

        freq.sort(key=lambda x: x["paper_count"], reverse=True)

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "total_methodologies": len(methodologies),
                "methodologies": freq[:max_results],
            },
        )
