"""Graph API service — builds a ResearchGraph and converts to DTOs."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.intelligence.graph.api.schemas import (
    GraphDTO,
    GraphEdgeDTO,
    GraphMetadataDTO,
    GraphNodeDTO,
    NodeType,
)
from app.modules.intelligence.graph.builder import PaperMetadata, ResearchGraphBuilder
from app.modules.intelligence.graph.models import ResearchGraph
from app.modules.investigation.service.service import InvestigationService
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)


class GraphApiService:
    """Service to build and serialise a research knowledge graph for the API.

    Uses the existing ``ResearchGraphBuilder`` and never modifies domain
    models.  Research domains are extracted from ``PaperNode`` metadata
    at the API layer rather than requiring a dedicated graph node type.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._inv_service = InvestigationService(db)
        self._extraction_repo = ExtractionRepository(db)
        self._paper_repo = PaperRepository(db)

    # ── Public API ────────────────────────────────────────────

    def get_graph(self, investigation_id: uuid.UUID) -> GraphDTO:
        """Build and return the knowledge graph DTO for an investigation."""
        inv = self._inv_service.get_investigation(investigation_id)
        if inv is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        records = self._extraction_repo.list_by_investigation(investigation_id)
        papers = self._paper_repo.list_by_investigation(investigation_id)

        paper_map = {}
        for p in papers:
            paper_map[str(p.id)] = PaperMetadata(
                year=p.year,
                citation_count=p.citation_count,
                venue=p.venue,
                authors=p.authors,
                doi=p.doi,
            )

        builder = ResearchGraphBuilder()
        graph = builder.build(records, paper_map=paper_map)

        return self._to_dto(graph)

    # ── DTO conversion ────────────────────────────────────────

    def _to_dto(self, graph: ResearchGraph) -> GraphDTO:
        nodes: list[GraphNodeDTO] = []
        edges: list[GraphEdgeDTO] = []
        seen_edges: set[str] = set()

        # Paper nodes
        for pid, paper in graph.papers.items():
            node_id = f"paper:{pid}"
            nodes.append(GraphNodeDTO(
                id=node_id,
                type=NodeType.PAPER,
                label=paper.title,
                metadata={
                    "id": pid,
                    "title": paper.title,
                    "year": paper.year,
                    "citation_count": paper.citation_count,
                    "venue": paper.venue,
                    "summary": self._extract_summary(paper.key_findings),
                    "methodology": paper.techniques[:3] if paper.techniques else [],
                    "datasets": [d.name for d in paper.datasets],
                    "technologies": [t.name for t in paper.technologies],
                    "authors": [a.name for a in paper.authors],
                    "institutions": [i.name for i in paper.institutions],
                    "research_domains": paper.research_domains,
                },
            ))

            # Author edges
            for author in paper.authors:
                target_id = f"author:{author.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="AUTHORED_BY", type="AUTHORED_BY",
                    ))

            # Institution edges
            for inst in paper.institutions:
                target_id = f"institution:{inst.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="BELONGS_TO", type="BELONGS_TO",
                    ))

            # Methodology edges
            for method in paper.methodologies:
                target_id = f"methodology:{method.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="INTRODUCES", type="INTRODUCES",
                    ))

            # Dataset edges
            for ds in paper.datasets:
                target_id = f"dataset:{ds.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="EVALUATED_ON", type="EVALUATED_ON",
                    ))

            # Technology edges
            for tech in paper.technologies:
                target_id = f"technology:{tech.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="USES", type="USES",
                    ))

            # Research domain edges (extracted from paper metadata)
            for rd in paper.research_domains:
                target_id = f"research_domain:{rd}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="RELATED_TO", type="RELATED_TO",
                    ))

        # Author nodes
        for name, author in graph.authors.items():
            node_id = f"author:{name}"
            nodes.append(GraphNodeDTO(
                id=node_id,
                type=NodeType.AUTHOR,
                label=name,
                metadata={
                    "name": name,
                    "papers": author.paper_ids,
                    "institution": (
                        author.affiliated_institutions[0].name
                        if author.affiliated_institutions else None
                    ),
                    "first_publication_year": author.first_publication_year,
                },
            ))

            # Author → Institution edges
            for inst in author.affiliated_institutions:
                target_id = f"institution:{inst.name}"
                edge_id = f"{node_id}->{target_id}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append(GraphEdgeDTO(
                        id=edge_id, source=node_id, target=target_id,
                        label="AFFILIATED_WITH", type="AFFILIATED_WITH",
                    ))

        # Institution nodes
        for name, inst in graph.institutions.items():
            nodes.append(GraphNodeDTO(
                id=f"institution:{name}",
                type=NodeType.INSTITUTION,
                label=name,
                metadata={
                    "name": name,
                    "type": inst.type.value if inst.type else None,
                    "country": inst.country,
                    "paper_count": len(inst.paper_ids),
                    "author_names": inst.author_names,
                },
            ))

        # Methodology nodes
        for name, method in graph.methodologies.items():
            nodes.append(GraphNodeDTO(
                id=f"methodology:{name}",
                type=NodeType.METHODOLOGY,
                label=name,
                metadata={
                    "name": name,
                    "related_papers": method.paper_ids,
                    "techniques": method.techniques,
                },
            ))

        # Dataset nodes
        for name, ds in graph.datasets.items():
            nodes.append(GraphNodeDTO(
                id=f"dataset:{name}",
                type=NodeType.DATASET,
                label=name,
                metadata={
                    "name": name,
                    "related_papers": ds.paper_ids,
                },
            ))

        # Technology nodes
        for name, tech in graph.technologies.items():
            nodes.append(GraphNodeDTO(
                id=f"technology:{name}",
                type=NodeType.TECHNOLOGY,
                label=name,
                metadata={
                    "name": name,
                    "type": tech.type.value if tech.type else None,
                    "related_papers": tech.paper_ids,
                },
            ))

        # Research Domain nodes (extracted from PaperNode metadata)
        all_domains: dict[str, list[str]] = {}
        for paper in graph.papers.values():
            for rd in paper.research_domains:
                all_domains.setdefault(rd, []).append(paper.id)

        for rd_name, paper_ids in all_domains.items():
            nodes.append(GraphNodeDTO(
                id=f"research_domain:{rd_name}",
                type=NodeType.RESEARCH_DOMAIN,
                label=rd_name,
                metadata={
                    "name": rd_name,
                    "related_papers": paper_ids,
                },
            ))

        # Compute metadata
        node_counts: dict[str, int] = {}
        for n in nodes:
            node_counts[n.type.value] = node_counts.get(n.type.value, 0) + 1

        edge_counts: dict[str, int] = {}
        for e in edges:
            edge_counts[e.type] = edge_counts.get(e.type, 0) + 1

        return GraphDTO(
            nodes=nodes,
            edges=edges,
            metadata=GraphMetadataDTO(
                total_nodes=len(nodes),
                total_edges=len(edges),
                node_counts=node_counts,
                edge_counts=edge_counts,
            ),
        )

    @staticmethod
    def _extract_summary(key_findings: list[str]) -> str:
        if not key_findings:
            return ""
        return " ".join(key_findings[:3])
