from __future__ import annotations

from collections.abc import Sequence

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalysisResults, AnalyzerResult
from app.modules.intelligence.context import AnalysisContext


class IntelligenceEngine:
    def __init__(
        self,
        context: AnalysisContext,
        *,
        auto_register: Sequence[type[BaseAnalyzer]] | None = None,
    ) -> None:
        self._context = context
        self._analyzers: dict[str, BaseAnalyzer] = {}
        if auto_register:
            for analyzer_cls in auto_register:
                self.register(analyzer_cls(context))

    def register(self, analyzer: BaseAnalyzer) -> None:
        if not analyzer.analyzer_name:
            raise ValueError("Analyzer must have a non-empty analyzer_name")
        self._analyzers[analyzer.analyzer_name] = analyzer

    def run(self) -> AnalysisResults:
        results: dict[str, AnalyzerResult] = {}
        for name, analyzer in self._analyzers.items():
            results[name] = analyzer.analyze()
        return AnalysisResults(
            results=results,
            investigation_id=self._context.investigation_id,
            execution_id=self._context.execution_id,
        )
