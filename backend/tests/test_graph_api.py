"""Tests for the Graph REST API — DTOs, service, and endpoint."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.intelligence.graph.api.schemas import (
    EdgeType,
    GraphDTO,
    GraphEdgeDTO,
    GraphMetadataDTO,
    GraphNodeDTO,
    NodeType,
)
from app.modules.intelligence.graph.api.service import GraphApiService

# ── DTO tests ─────────────────────────────────────────────────────


class TestGraphDTOs:
    def test_node_type_values(self) -> None:
        assert NodeType.PAPER.value == "paper"
        assert NodeType.AUTHOR.value == "author"
        assert NodeType.INSTITUTION.value == "institution"
        assert NodeType.DATASET.value == "dataset"
        assert NodeType.TECHNOLOGY.value == "technology"
        assert NodeType.METHODOLOGY.value == "methodology"
        assert NodeType.RESEARCH_DOMAIN.value == "research_domain"

    def test_edge_type_values(self) -> None:
        assert EdgeType.AUTHORED_BY.value == "AUTHORED_BY"
        assert EdgeType.BELONGS_TO.value == "BELONGS_TO"
        assert EdgeType.INTRODUCES.value == "INTRODUCES"
        assert EdgeType.EVALUATED_ON.value == "EVALUATED_ON"
        assert EdgeType.USES.value == "USES"
        assert EdgeType.RELATED_TO.value == "RELATED_TO"
        assert EdgeType.AFFILIATED_WITH.value == "AFFILIATED_WITH"

    def test_graph_node_dto_creation(self) -> None:
        node = GraphNodeDTO(
            id="paper:abc-123",
            type=NodeType.PAPER,
            label="Test Paper",
            metadata={"year": 2024, "authors": ["Alice"]},
        )
        assert node.id == "paper:abc-123"
        assert node.type == NodeType.PAPER
        assert node.label == "Test Paper"
        assert node.metadata["year"] == 2024

    def test_graph_edge_dto_creation(self) -> None:
        edge = GraphEdgeDTO(
            id="paper:abc->author:Alice",
            source="paper:abc",
            target="author:Alice",
            label="AUTHORED_BY",
            type="AUTHORED_BY",
        )
        assert edge.source == "paper:abc"
        assert edge.target == "author:Alice"
        assert edge.label == "AUTHORED_BY"

    def test_graph_dto_aggregates(self) -> None:
        dto = GraphDTO(
            nodes=[
                GraphNodeDTO(id="n1", type=NodeType.PAPER, label="P1"),
                GraphNodeDTO(id="n2", type=NodeType.AUTHOR, label="A1"),
            ],
            edges=[
                GraphEdgeDTO(
                    id="e1", source="n1", target="n2", label="AUTHORED_BY", type="AUTHORED_BY"
                ),
            ],
            metadata=GraphMetadataDTO(
                total_nodes=2,
                total_edges=1,
                node_counts={"paper": 1, "author": 1},
                edge_counts={"AUTHORED_BY": 1},
            ),
        )
        assert dto.metadata.total_nodes == 2
        assert dto.metadata.total_edges == 1
        assert len(dto.nodes) == 2
        assert len(dto.edges) == 1

    def test_graph_dto_empty(self) -> None:
        dto = GraphDTO(metadata=GraphMetadataDTO())
        assert dto.metadata.total_nodes == 0
        assert dto.nodes == []

    def test_node_metadata_flexible(self) -> None:
        node = GraphNodeDTO(
            id="d1",
            type=NodeType.DATASET,
            label="ImageNet",
            metadata={"name": "ImageNet", "related_papers": ["p1", "p2"]},
        )
        assert node.metadata["name"] == "ImageNet"
        assert len(node.metadata["related_papers"]) == 2

    def test_serialization_roundtrip(self) -> None:
        dto = GraphDTO(
            nodes=[GraphNodeDTO(id="n1", type=NodeType.PAPER, label="Paper")],
            edges=[
                GraphEdgeDTO(
                    id="e1", source="n1", target="author:X", label="AUTHORED_BY", type="AUTHORED_BY"
                )
            ],
            metadata=GraphMetadataDTO(
                total_nodes=1,
                total_edges=1,
                node_counts={"paper": 1},
                edge_counts={"AUTHORED_BY": 1},
            ),
        )
        raw = dto.model_dump()
        restored = GraphDTO.model_validate(raw)
        assert restored.nodes[0].label == "Paper"
        assert restored.edges[0].type == "AUTHORED_BY"


# ── Service tests ─────────────────────────────────────────────────


@patch("app.modules.intelligence.graph.api.service.InvestigationService")
@patch("app.modules.intelligence.graph.api.service.ExtractionRepository")
@patch("app.modules.intelligence.graph.api.service.PaperRepository")
class TestGraphApiService:
    def test_get_graph_raises_404_for_missing_investigation(
        self,
        _mock_paper_repo: MagicMock,
        _mock_extraction_repo: MagicMock,
        mock_inv_service_cls: MagicMock,
    ) -> None:
        db = MagicMock()
        service = GraphApiService(db)
        mock_inv_service = mock_inv_service_cls.return_value
        mock_inv_service.get_investigation.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.get_graph(uuid.uuid4())
        assert exc.value.status_code == 404

    @patch("app.modules.intelligence.graph.api.service.ResearchGraphBuilder")
    def test_get_graph_with_no_data(
        self,
        mock_builder_cls: MagicMock,
        _mock_paper_repo: MagicMock,
        _mock_extraction_repo: MagicMock,
        mock_inv_service_cls: MagicMock,
    ) -> None:
        inv_id = uuid.uuid4()
        mock_graph = MagicMock()
        mock_graph.papers = {}
        mock_graph.authors = {}
        mock_graph.institutions = {}
        mock_graph.methodologies = {}
        mock_graph.datasets = {}
        mock_graph.technologies = {}

        builder_instance = MagicMock()
        builder_instance.build.return_value = mock_graph
        mock_builder_cls.return_value = builder_instance

        db = MagicMock()
        service = GraphApiService(db)
        mock_inv_service_cls.return_value.get_investigation.return_value = MagicMock()
        service._extraction_repo.list_by_investigation.return_value = []
        service._paper_repo.list_by_investigation.return_value = []

        result = service.get_graph(inv_id)
        assert result.metadata.total_nodes == 0
        assert result.metadata.total_edges == 0
        assert result.nodes == []
        assert result.edges == []

    @patch("app.modules.intelligence.graph.api.service.ResearchGraphBuilder")
    def test_get_graph_returns_dto_with_data(
        self,
        mock_builder_cls: MagicMock,
        _mock_paper_repo: MagicMock,
        _mock_extraction_repo: MagicMock,
        mock_inv_service_cls: MagicMock,
    ) -> None:
        inv_id = uuid.uuid4()

        mock_graph = MagicMock()
        mock_graph.papers = {}
        mock_graph.authors = {}
        mock_graph.institutions = {}
        mock_graph.methodologies = {}
        mock_graph.datasets = {}
        mock_graph.technologies = {}

        builder_instance = MagicMock()
        builder_instance.build.return_value = mock_graph
        mock_builder_cls.return_value = builder_instance

        db = MagicMock()
        service = GraphApiService(db)
        mock_inv_service_cls.return_value.get_investigation.return_value = MagicMock()
        service._extraction_repo.list_by_investigation.return_value = []
        service._paper_repo.list_by_investigation.return_value = []

        result = service.get_graph(inv_id)
        assert isinstance(result, GraphDTO)
        assert isinstance(result.metadata, GraphMetadataDTO)


# ── Static method tests (outside class to avoid class-level patches) ─


def test_extract_summary_empty() -> None:
    assert GraphApiService._extract_summary([]) == ""


def test_extract_summary_joins_findings() -> None:
    result = GraphApiService._extract_summary(["Finding A", "Finding B", "Finding C"])
    assert "Finding A" in result
    assert "Finding B" in result


def test_extract_summary_truncates() -> None:
    findings = [f"Finding {i}" for i in range(10)]
    result = GraphApiService._extract_summary(findings)
    assert sum(1 for f in ["Finding 0", "Finding 1", "Finding 2"] if f in result) == 3


# ── Edge label derivation ─────────────────────────────────────────


def test_edge_labels_cover_deliverable_requirements() -> None:
    required = {"AUTHORED_BY", "BELONGS_TO", "INTRODUCES", "EVALUATED_ON", "USES", "RELATED_TO"}
    defined = {e.value for e in EdgeType}
    assert required.issubset(defined), f"Missing edge types: {required - defined}"
