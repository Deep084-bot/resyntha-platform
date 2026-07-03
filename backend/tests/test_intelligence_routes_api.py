"""Tests for the Intelligence REST API routes and schemas."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.v1 import v1_router
from app.modules.artifact.domain.models import ArtifactStatus, ArtifactType
from app.modules.artifact.schemas.response import ArtifactResponse
from app.modules.intelligence.api.dependencies import (
    get_artifact_service,
    get_investigation_service,
)
from app.modules.intelligence.api.schemas import (
    CentralityEntryResponse,
    CollaborationPairResponse,
    CollaborationSectionResponse,
    DatasetSectionResponse,
    InstitutionEntryResponse,
    InstitutionSectionResponse,
    LandscapeResponse,
    MarkdownResponse,
    MethodologyEntryResponse,
    MethodologySectionResponse,
    NetworkResponse,
    ObservationResponse,
    OverviewSectionResponse,
    TechnologySectionResponse,
    TemporalSectionResponse,
    TopEntityResponse,
)
from app.modules.investigation.schemas.response import InvestigationResponse

# =============================================================================
# Fixtures — JSON renderer output matching real artifact payloads
# =============================================================================


@pytest.fixture
def inv_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def full_landscape_json() -> dict[str, Any]:
    return {
        "overview": {
            "total_papers": 10,
            "years_covered": [2022, 2023, 2024],
            "total_institutions": 2,
            "total_methodologies": 2,
            "total_technologies": 2,
            "total_datasets": 2,
            "total_authors": 4,
        },
        "institutions": {
            "total": 2,
            "type_distribution": {"university": 1, "company": 1},
            "top_institutions": [
                {
                    "name": "MIT",
                    "type": "university",
                    "paper_count": 10,
                    "author_count": 5,
                },
                {
                    "name": "Google",
                    "type": "company",
                    "paper_count": 3,
                    "author_count": 2,
                },
            ],
        },
        "methodologies": {
            "total": 2,
            "methodologies": [
                {
                    "name": "CNN",
                    "paper_count": 8,
                    "technique_count": 2,
                    "techniques": ["conv", "pool"],
                },
                {
                    "name": "RNN",
                    "paper_count": 3,
                    "technique_count": 1,
                    "techniques": ["backprop"],
                },
            ],
        },
        "technologies": {
            "total": 2,
            "top_technologies": [
                {"name": "PyTorch", "paper_count": 5},
                {"name": "JAX", "paper_count": 3},
            ],
            "first_appearance_by_year": {"PyTorch": 2022, "JAX": 2024},
            "diversity": {
                "total_technologies": 2,
                "papers_with_technology": 8,
                "avg_papers_per_technology": 4.0,
            },
        },
        "datasets": {
            "total": 2,
            "top_datasets": [
                {"name": "ImageNet", "paper_count": 4},
                {"name": "COCO", "paper_count": 3},
            ],
            "diversity": {
                "total_datasets": 2,
                "papers_with_dataset": 7,
                "avg_papers_per_dataset": 3.5,
            },
        },
        "temporal": {
            "years_covered": [2022, 2023, 2024],
            "total_papers": 10,
            "papers_per_year": {2022: 4, 2023: 3, 2024: 3},
        },
        "collaborations": {
            "institution_network": {
                "total_nodes": 3,
                "total_edges": 2,
                "degree_centrality": {"MIT": 0.8, "Stanford": 0.6},
                "top_by_centrality": [
                    {"name": "MIT", "centrality": 0.8},
                    {"name": "Stanford", "centrality": 0.6},
                ],
            },
            "institution_collaborations": [
                {"source": "MIT", "target": "Stanford", "weight": 2},
            ],
            "author_network": {
                "total_nodes": 4,
                "total_edges": 3,
                "degree_centrality": {"Alice": 0.9, "Bob": 0.7},
                "top_by_centrality": [
                    {"name": "Alice", "centrality": 0.9},
                ],
            },
            "author_collaborations": [
                {"source": "Alice", "target": "Bob", "weight": 3},
            ],
        },
        "observations": [
            {"category": "institution", "label": "Most active institution", "value": "MIT"},
            {"category": "methodology", "label": "Most common methodology", "value": "CNN"},
        ],
    }


@pytest.fixture
def full_markdown_content() -> str:
    return """# Research Landscape

## Overview
| Metric | Value |
| --- | --- |
| Total Papers | 10 |

## Institutions
...
"""


@pytest.fixture
def mock_inv_service(inv_id: uuid.UUID) -> MagicMock:
    svc = MagicMock()
    svc.get_investigation.return_value = InvestigationResponse(
        id=inv_id,
        title="Test Investigation",
        topic="Test Topic",
        status="created",
        paper_limit=50,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        metadata={},
    )
    return svc


@pytest.fixture
def mock_artifact_service_json(
    inv_id: uuid.UUID,
    full_landscape_json: dict[str, Any],
) -> MagicMock:
    svc = MagicMock()
    svc.list_artifacts.return_value = [
        ArtifactResponse(
            id=uuid.uuid4(),
            investigation_id=inv_id,
            artifact_type=ArtifactType.RESEARCH_LANDSCAPE,
            version=1,
            status=ArtifactStatus.READY,
            payload={
                "format": "json",
                "content": full_landscape_json,
                "investigation_id": str(inv_id),
                "generated_at": datetime.now(UTC).isoformat(),
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]
    return svc


@pytest.fixture
def mock_artifact_service_markdown(
    inv_id: uuid.UUID,
    full_markdown_content: str,
) -> MagicMock:
    svc = MagicMock()
    svc.list_artifacts.return_value = [
        ArtifactResponse(
            id=uuid.uuid4(),
            investigation_id=inv_id,
            artifact_type=ArtifactType.RESEARCH_LANDSCAPE,
            version=1,
            status=ArtifactStatus.READY,
            payload={
                "format": "markdown",
                "content": full_markdown_content,
                "investigation_id": str(inv_id),
                "generated_at": datetime.now(UTC).isoformat(),
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]
    return svc


@pytest.fixture
def mock_inv_service_not_found() -> MagicMock:
    svc = MagicMock()
    svc.get_investigation.return_value = None
    return svc


@pytest.fixture
def mock_artifact_service_empty(
    inv_id: uuid.UUID,
) -> MagicMock:
    svc = MagicMock()
    svc.list_artifacts.return_value = []
    return svc


# =============================================================================
# Schema tests — deserialisation from JSON artifact content
# =============================================================================


class TestLandscapeSchema:
    def test_deserialise_full(
        self,
        full_landscape_json: dict[str, Any],
    ) -> None:
        result = LandscapeResponse.model_validate(full_landscape_json)
        assert isinstance(result, LandscapeResponse)
        assert isinstance(result, BaseModel)

        assert result.overview is not None
        assert result.overview.total_papers == 10
        assert result.overview.years_covered == [2022, 2023, 2024]

        assert result.institutions is not None
        assert result.institutions.total == 2
        assert len(result.institutions.top_institutions) == 2
        assert result.institutions.top_institutions[0].name == "MIT"
        assert result.institutions.top_institutions[0].paper_count == 10

        assert result.methodologies is not None
        assert result.methodologies.total == 2
        assert result.methodologies.methodologies[0].name == "CNN"

        assert result.technologies is not None
        assert result.technologies.total == 2
        assert result.technologies.top_technologies[0].name == "PyTorch"
        assert result.technologies.diversity is not None
        assert result.technologies.diversity.total_technologies == 2

        assert result.datasets is not None
        assert result.datasets.total == 2
        assert result.datasets.diversity is not None
        assert result.datasets.diversity.total_datasets == 2

        assert result.temporal is not None
        assert result.temporal.total_papers == 10
        assert result.temporal.papers_per_year == {2022: 4, 2023: 3, 2024: 3}

        assert result.collaborations is not None
        assert result.collaborations.institution_network is not None
        assert result.collaborations.institution_network.total_nodes == 3
        assert result.collaborations.author_network is not None
        assert result.collaborations.author_network.total_nodes == 4

        assert result.observations is not None
        assert len(result.observations) == 2
        assert result.observations[0].label == "Most active institution"

    def test_deserialise_empty(self) -> None:
        result = LandscapeResponse.model_validate({})
        assert result.overview is None
        assert result.institutions is None
        assert result.methodologies is None
        assert result.technologies is None
        assert result.datasets is None
        assert result.temporal is None
        assert result.collaborations is None
        assert result.observations is None

    def test_deserialise_partial(self) -> None:
        data = {
            "overview": {"total_papers": 5},
            "institutions": {"total": 1},
        }
        result = LandscapeResponse.model_validate(data)
        assert result.overview is not None
        assert result.overview.total_papers == 5
        assert result.institutions is not None
        assert result.institutions.total == 1
        assert result.methodologies is None
        assert result.technologies is None
        assert result.datasets is None
        assert result.temporal is None
        assert result.collaborations is None
        assert result.observations is None

    def test_deterministic(self, full_landscape_json: dict[str, Any]) -> None:
        r1 = LandscapeResponse.model_validate(full_landscape_json)
        r2 = LandscapeResponse.model_validate(full_landscape_json)
        assert r1.model_dump() == r2.model_dump()

    def test_overview_section_deserialise(self) -> None:
        raw = {"total_papers": 5, "years_covered": [2020]}
        result = OverviewSectionResponse.model_validate(raw)
        assert result.total_papers == 5
        assert result.years_covered == [2020]

    def test_institution_section_deserialise(self) -> None:
        raw = {
            "total": 1,
            "type_distribution": {"university": 1},
            "top_institutions": [
                {"name": "MIT", "type": "university", "paper_count": 10, "author_count": 5},
            ],
        }
        result = InstitutionSectionResponse.model_validate(raw)
        assert result.total == 1
        assert len(result.top_institutions) == 1
        assert result.top_institutions[0].name == "MIT"

    def test_methodology_section_deserialise(self) -> None:
        raw = {
            "total": 1,
            "methodologies": [
                {"name": "CNN", "paper_count": 8, "technique_count": 2, "techniques": ["conv"]},
            ],
        }
        result = MethodologySectionResponse.model_validate(raw)
        assert result.total == 1
        assert result.methodologies[0].name == "CNN"

    def test_technology_section_deserialise(self) -> None:
        raw = {
            "total": 1,
            "top_technologies": [{"name": "PyTorch", "paper_count": 5}],
            "first_appearance_by_year": {"PyTorch": 2022},
            "diversity": {
                "total_technologies": 1,
                "papers_with_technology": 5,
                "avg_papers_per_technology": 5.0,
            },
        }
        result = TechnologySectionResponse.model_validate(raw)
        assert result.total == 1
        assert result.top_technologies[0].name == "PyTorch"
        assert result.diversity is not None
        assert result.diversity.avg_papers_per_technology == 5.0

    def test_dataset_section_deserialise(self) -> None:
        raw = {
            "total": 1,
            "top_datasets": [{"name": "ImageNet", "paper_count": 4}],
            "diversity": {
                "total_datasets": 1,
                "papers_with_dataset": 4,
                "avg_papers_per_dataset": 4.0,
            },
        }
        result = DatasetSectionResponse.model_validate(raw)
        assert result.total == 1
        assert result.top_datasets[0].name == "ImageNet"

    def test_temporal_section_deserialise(self) -> None:
        raw = {
            "years_covered": [2022, 2023],
            "total_papers": 10,
            "papers_per_year": {2022: 4, 2023: 6},
        }
        result = TemporalSectionResponse.model_validate(raw)
        assert result.total_papers == 10
        assert result.papers_per_year[2022] == 4

    def test_collaboration_section_deserialise(self) -> None:
        raw = {
            "institution_network": {
                "total_nodes": 3,
                "total_edges": 2,
                "degree_centrality": {"MIT": 0.8},
                "top_by_centrality": [{"name": "MIT", "centrality": 0.8}],
            },
            "institution_collaborations": [
                {"source": "MIT", "target": "Stanford", "weight": 2},
            ],
        }
        result = CollaborationSectionResponse.model_validate(raw)
        assert result.institution_network is not None
        assert result.institution_network.total_nodes == 3
        assert result.institution_collaborations is not None
        assert result.institution_collaborations[0].source == "MIT"
        assert result.author_network is None

    def test_markdown_response(self) -> None:
        result = MarkdownResponse(markdown="# Hello")
        assert result.markdown == "# Hello"

    def test_observation_response(self) -> None:
        result = ObservationResponse(category="a", label="b", value="c")
        assert result.category == "a"
        assert result.label == "b"
        assert result.value == "c"

    def test_institution_entry_defaults(self) -> None:
        result = InstitutionEntryResponse(
            name="MIT", type="university", paper_count=0, author_count=0
        )
        assert result.name == "MIT"
        assert result.paper_count == 0

    def test_methodology_entry_defaults(self) -> None:
        result = MethodologyEntryResponse(name="CNN", paper_count=5)
        assert result.technique_count == 0
        assert result.techniques == []

    def test_top_entity_response(self) -> None:
        result = TopEntityResponse(name="PyTorch", paper_count=5)
        assert result.name == "PyTorch"
        assert result.paper_count == 5

    def test_network_response(self) -> None:
        result = NetworkResponse(
            total_nodes=3,
            total_edges=2,
            degree_centrality={"A": 0.9},
            top_by_centrality=[CentralityEntryResponse(name="A", centrality=0.9)],
        )
        assert result.total_nodes == 3
        assert result.top_by_centrality[0].centrality == 0.9

    def test_collaboration_pair(self) -> None:
        result = CollaborationPairResponse(source="A", target="B", weight=5)
        assert result.source == "A"
        assert result.weight == 5


# =============================================================================
# Route tests — via TestClient with mocked dependencies
# =============================================================================


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


def _override_deps(
    app: FastAPI,
    inv_service: MagicMock | None = None,
    art_service: MagicMock | None = None,
) -> None:
    def _inv() -> MagicMock:
        return inv_service or MagicMock()

    def _art() -> MagicMock:
        return art_service or MagicMock()

    app.dependency_overrides[get_investigation_service] = _inv
    app.dependency_overrides[get_artifact_service] = _art


class TestGetLandscape:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/landscape")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["overview"]["total_papers"] == 10
        assert body["institutions"]["total"] == 2
        assert body["methodologies"]["total"] == 2
        assert body["technologies"]["total"] == 2
        assert body["datasets"]["total"] == 2
        assert body["temporal"]["total_papers"] == 10
        assert "collaborations" in body
        assert len(body["observations"]) == 2

    def test_404_investigation_not_found(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service_not_found: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service_not_found, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/landscape")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_404_artifact_not_found(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_empty: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_empty)
        resp = client.get(f"/investigations/{inv_id}/landscape")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_deterministic(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        r1 = client.get(f"/investigations/{inv_id}/landscape").json()
        r2 = client.get(f"/investigations/{inv_id}/landscape").json()
        assert r1 == r2

    def test_schema_enforced(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/landscape")
        body = resp.json()
        assert isinstance(body["overview"]["total_papers"], int)
        assert isinstance(body["institutions"]["top_institutions"], list)
        assert isinstance(body["observations"], list)


class TestGetLandscapeMarkdown:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_markdown: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_markdown)
        resp = client.get(f"/investigations/{inv_id}/landscape/markdown")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["markdown"].startswith("# Research Landscape")

    def test_404_investigation(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service_not_found: MagicMock,
        mock_artifact_service_markdown: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service_not_found, mock_artifact_service_markdown)
        resp = client.get(f"/investigations/{inv_id}/landscape/markdown")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_404_artifact(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_empty: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_empty)
        resp = client.get(f"/investigations/{inv_id}/landscape/markdown")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestGetLandscapeJson:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
        full_landscape_json: dict[str, Any],
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/landscape/json")
        assert resp.status_code == status.HTTP_200_OK
        # Compare through JSON round-trip to account for int→str key coercion
        assert resp.json() == json.loads(json.dumps(full_landscape_json))

    def test_404(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service_not_found: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service_not_found, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/landscape/json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestGetOverview:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/overview")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total_papers"] == 10
        assert body["years_covered"] == [2022, 2023, 2024]

    def test_404(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service_not_found: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service_not_found, MagicMock())
        resp = client.get(f"/investigations/{inv_id}/overview")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestGetInstitutions:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/institutions")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 2
        assert body["top_institutions"][0]["name"] == "MIT"


class TestGetMethodologies:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/methodologies")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 2
        assert body["methodologies"][0]["name"] == "CNN"


class TestGetTechnologies:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/technologies")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 2
        assert body["top_technologies"][0]["name"] == "PyTorch"


class TestGetDatasets:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/datasets")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 2
        assert body["top_datasets"][0]["name"] == "ImageNet"


class TestGetTemporal:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/temporal")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total_papers"] == 10
        assert body["papers_per_year"]["2022"] == 4


class TestGetCollaborations:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_inv_service: MagicMock,
        mock_artifact_service_json: MagicMock,
    ) -> None:
        _override_deps(test_app, mock_inv_service, mock_artifact_service_json)
        resp = client.get(f"/investigations/{inv_id}/collaborations")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["institution_network"]["total_nodes"] == 3
        assert body["author_network"]["total_nodes"] == 4
        assert len(body["institution_collaborations"]) == 1
