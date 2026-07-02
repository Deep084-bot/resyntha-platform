from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.intelligence.analyzers.models import AnalyzerResult
from app.modules.intelligence.config import IntelligenceConfig
from app.modules.intelligence.context import AnalysisContext
from app.modules.intelligence.graph.models import ResearchGraph


class BaseAnalyzer(ABC):
    analyzer_name: str = ""

    def __init__(self, context: AnalysisContext) -> None:
        self.context = context
        self.graph: ResearchGraph = context.graph
        self.config: IntelligenceConfig = context.config

    @abstractmethod
    def analyze(self) -> AnalyzerResult:
        ...
