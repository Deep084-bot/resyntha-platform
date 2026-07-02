from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalyzerResult:
    analyzer_name: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResults:
    results: dict[str, AnalyzerResult] = field(default_factory=dict)
    investigation_id: str = ""
    execution_id: str | None = None

    def __getitem__(self, name: str) -> AnalyzerResult:
        return self.results[name]

    @property
    def analyzer_names(self) -> list[str]:
        return list(self.results.keys())
