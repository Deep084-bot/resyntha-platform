"""Graph DTOs exposed by the Intelligence Graph REST API.

These are API-friendly serialisation models, not ORM entities.
Do NOT import domain/graph models here.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel


class NodeType(enum.StrEnum):
    PAPER = "paper"
    AUTHOR = "author"
    INSTITUTION = "institution"
    DATASET = "dataset"
    TECHNOLOGY = "technology"
    METHODOLOGY = "methodology"
    RESEARCH_DOMAIN = "research_domain"


class EdgeType(enum.StrEnum):
    AUTHORED_BY = "AUTHORED_BY"
    BELONGS_TO = "BELONGS_TO"
    INTRODUCES = "INTRODUCES"
    EVALUATED_ON = "EVALUATED_ON"
    USES = "USES"
    RELATED_TO = "RELATED_TO"
    AFFILIATED_WITH = "AFFILIATED_WITH"


class GraphNodeDTO(BaseModel):
    id: str
    type: NodeType
    label: str
    metadata: dict = {}


class GraphEdgeDTO(BaseModel):
    id: str
    source: str
    target: str
    label: str
    type: str


class GraphMetadataDTO(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    node_counts: dict[str, int] = {}
    edge_counts: dict[str, int] = {}


class GraphDTO(BaseModel):
    nodes: list[GraphNodeDTO] = []
    edges: list[GraphEdgeDTO] = []
    metadata: GraphMetadataDTO
