"""Research Intelligence Engine.

Transforms extracted knowledge into structured intelligence via
a normalized ResearchGraph and composable analyzers.
"""

from app.modules.intelligence.analyzers import (
    AnalysisResults,
    AnalyzerResult,
    BaseAnalyzer,
    InstitutionAnalyzer,
    IntelligenceEngine,
    MethodologyAnalyzer,
    TemporalAnalyzer,
)
from app.modules.intelligence.config import IntelligenceConfig
from app.modules.intelligence.context import AnalysisContext
from app.modules.intelligence.graph import (
    AuthorNode,
    DatasetNode,
    EntityResolver,
    GraphServices,
    InstitutionNode,
    InstitutionType,
    MethodologyNode,
    MetricNode,
    PaperMetadata,
    PaperNode,
    ResearchGraph,
    ResearchGraphBuilder,
    TechnologyNode,
    TechnologyType,
)
from app.modules.intelligence.services import (
    CentralityService,
    CoOccurrenceService,
    SimilarityService,
    StatisticsService,
    TrendService,
)

__all__ = [
    "AnalysisContext",
    "AnalysisResults",
    "AnalyzerResult",
    "AuthorNode",
    "BaseAnalyzer",
    "CentralityService",
    "CoOccurrenceService",
    "DatasetNode",
    "EntityResolver",
    "GraphServices",
    "InstitutionAnalyzer",
    "InstitutionNode",
    "InstitutionType",
    "IntelligenceConfig",
    "IntelligenceEngine",
    "MethodologyAnalyzer",
    "MethodologyNode",
    "MetricNode",
    "PaperMetadata",
    "PaperNode",
    "ResearchGraph",
    "ResearchGraphBuilder",
    "SimilarityService",
    "StatisticsService",
    "TechnologyNode",
    "TechnologyType",
    "TemporalAnalyzer",
    "TrendService",
]
