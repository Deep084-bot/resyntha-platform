"""ResearchGraph — in-memory entity graph for the Intelligence Engine."""

from app.modules.intelligence.graph.builder import PaperMetadata, ResearchGraphBuilder
from app.modules.intelligence.graph.models import (
    AuthorNode,
    DatasetNode,
    GraphServices,
    InstitutionNode,
    InstitutionType,
    MethodologyNode,
    MetricNode,
    PaperNode,
    ResearchGraph,
    TechnologyNode,
    TechnologyType,
)
from app.modules.intelligence.graph.resolver import EntityResolver

# API DTOs
from app.modules.intelligence.graph.api.schemas import (
    EdgeType,
    GraphDTO,
    GraphEdgeDTO,
    GraphMetadataDTO,
    GraphNodeDTO,
    NodeType,
)
from app.modules.intelligence.graph.api.service import GraphApiService

__all__ = [
    "AuthorNode",
    "DatasetNode",
    "EdgeType",
    "EntityResolver",
    "GraphApiService",
    "GraphDTO",
    "GraphEdgeDTO",
    "GraphMetadataDTO",
    "GraphNodeDTO",
    "GraphServices",
    "InstitutionNode",
    "InstitutionType",
    "MethodologyNode",
    "MetricNode",
    "NodeType",
    "PaperMetadata",
    "PaperNode",
    "ResearchGraph",
    "ResearchGraphBuilder",
    "TechnologyNode",
    "TechnologyType",
]
