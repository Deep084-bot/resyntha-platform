"""Tests for Institution Intelligence — profile service, domain models, and API routes."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.v1 import v1_router
from app.modules.institution.api.dependencies import (
    get_institution_profile_service,
)
from app.modules.institution.api.schemas import (
    AuthorEntryResponse,
    CollaborationEntryResponse,
    CompareRequest,
    EntityCountResponse,
    InstitutionProfileResponse,
    PaperEntryResponse,
    YearlyTrendResponse,
)
from app.modules.institution.domain.models import (
    AuthorEntry,
    CollaborationEntry,
    EntityCount,
    InstitutionProfile,
    PaperEntry,
    YearlyTrend,
)
from app.modules.institution.service.service import InstitutionProfileService

# =============================================================================
# Domain model tests
# =============================================================================


class TestDomainModels:
    def test_entity_count(self) -> None:
        ec = EntityCount(name="CNN", count=10)
        assert ec.name == "CNN"
        assert ec.count == 10

    def test_author_entry(self) -> None:
        ae = AuthorEntry(name="Alice", paper_count=5, affiliated_institutions=["MIT"])
        assert ae.name == "Alice"
        assert ae.paper_count == 5
        assert ae.affiliated_institutions == ["MIT"]

    def test_author_entry_defaults(self) -> None:
        ae = AuthorEntry(name="Bob", paper_count=3)
        assert ae.affiliated_institutions == []

    def test_paper_entry(self) -> None:
        pe = PaperEntry(
            id="p1",
            title="Test Paper",
            year=2024,
            citation_count=10,
            venue="NeurIPS",
            authors=["Alice"],
            research_domains=["ML"],
        )
        assert pe.id == "p1"
        assert pe.title == "Test Paper"
        assert pe.year == 2024
        assert pe.citation_count == 10

    def test_paper_entry_defaults(self) -> None:
        pe = PaperEntry(id="p1", title="Test")
        assert pe.year is None
        assert pe.authors == []

    def test_collaboration_entry(self) -> None:
        ce = CollaborationEntry(institution_name="Stanford", joint_paper_count=3)
        assert ce.institution_name == "Stanford"
        assert ce.joint_paper_count == 3

    def test_yearly_trend(self) -> None:
        yt = YearlyTrend(year=2023, paper_count=5)
        assert yt.year == 2023
        assert yt.paper_count == 5

    def test_institution_profile(self) -> None:
        profile = InstitutionProfile(
            name="MIT",
            type="university",
            total_papers=10,
            total_authors=5,
            total_citations=100,
        )
        assert profile.name == "MIT"
        assert profile.total_papers == 10
        assert profile.research_domains == []
        assert profile.technologies == []


# =============================================================================
# Schema tests
# =============================================================================


class TestSchemas:
    def test_entity_count_response(self) -> None:
        r = EntityCountResponse(name="CNN", count=10)
        assert r.name == "CNN"
        assert r.count == 10

    def test_author_entry_response(self) -> None:
        r = AuthorEntryResponse(name="Alice", paper_count=5, affiliated_institutions=["MIT"])
        assert r.name == "Alice"
        assert r.paper_count == 5
        assert r.affiliated_institutions == ["MIT"]

    def test_paper_entry_response(self) -> None:
        r = PaperEntryResponse(
            id="p1",
            title="Test",
            year=2024,
            citation_count=10,
            venue="NeurIPS",
            authors=["Alice"],
            research_domains=["ML"],
        )
        assert r.id == "p1"
        assert r.title == "Test"

    def test_collaboration_entry_response(self) -> None:
        r = CollaborationEntryResponse(institution_name="Stanford", joint_paper_count=3)
        assert r.institution_name == "Stanford"

    def test_yearly_trend_response(self) -> None:
        r = YearlyTrendResponse(year=2023, paper_count=5)
        assert r.year == 2023

    def test_institution_profile_response(self) -> None:
        r = InstitutionProfileResponse(
            name="MIT",
            type="university",
            total_papers=10,
            total_authors=5,
            total_citations=100,
        )
        assert r.name == "MIT"
        assert r.total_papers == 10
        assert r.research_domains == []

    def test_institution_profile_response_full(self) -> None:
        r = InstitutionProfileResponse(
            name="Stanford",
            type="university",
            total_papers=20,
            total_authors=10,
            total_citations=200,
            research_domains=[EntityCountResponse(name="ML", count=15)],
            technologies=[EntityCountResponse(name="PyTorch", count=12)],
            datasets=[EntityCountResponse(name="ImageNet", count=8)],
            methodologies=[EntityCountResponse(name="CNN", count=10)],
            top_authors=[AuthorEntryResponse(name="Alice", paper_count=10)],
            top_papers=[PaperEntryResponse(id="p1", title="Paper")],
            yearly_trends=[YearlyTrendResponse(year=2024, paper_count=5)],
            collaborating_institutions=[
                CollaborationEntryResponse(institution_name="MIT", joint_paper_count=3)
            ],
            co_authors=[AuthorEntryResponse(name="Bob", paper_count=2)],
        )
        assert r.name == "Stanford"
        assert r.research_domains[0].name == "ML"
        assert r.top_authors[0].name == "Alice"
        assert r.yearly_trends[0].year == 2024

    def test_compare_request(self) -> None:
        r = CompareRequest(institution_names=["MIT", "Stanford"])
        assert r.institution_names == ["MIT", "Stanford"]
        assert len(r.institution_names) == 2


# =============================================================================
# Service tests — mocked graph
# =============================================================================


@pytest.fixture
def mock_institution_node() -> MagicMock:
    node = MagicMock()
    node.name = "MIT"
    node.type.value = "university"
    node.paper_ids = ["p1", "p2", "p3"]
    node.author_names = ["Alice", "Bob"]
    return node


@pytest.fixture
def mock_graph_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_graph_service: MagicMock) -> InstitutionProfileService:
    return InstitutionProfileService(mock_graph_service)


class TestServiceListProfiles:
    def test_empty_graph_returns_empty_list(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {}
        mock_graph_service.get_raw_graph.return_value = mock_graph

        result = service.list_profiles(uuid.uuid4())
        assert result == []

    def test_returns_sorted_profiles(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        inst1 = MagicMock()
        inst1.name = "MIT"
        inst1.type.value = "university"
        inst1.paper_ids = ["p1", "p2", "p3"]
        inst1.author_names = ["A", "B"]

        inst2 = MagicMock()
        inst2.name = "Stanford"
        inst2.type.value = "university"
        inst2.paper_ids = ["p1"]
        inst2.author_names = ["C"]

        mock_graph = MagicMock()
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}
        mock_graph.papers = {}
        mock_graph.authors = {}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        result = service.list_profiles(uuid.uuid4())
        assert len(result) == 2
        assert result[0].name == "MIT"
        assert result[1].name == "Stanford"

    def test_profile_has_correct_fields(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        inst = MagicMock()
        inst.name = "MIT"
        inst.type.value = "university"
        inst.paper_ids = ["p1"]
        inst.author_names = ["Alice"]

        paper = MagicMock()
        paper.id = "p1"
        paper.title = "Paper 1"
        paper.year = 2024
        paper.citation_count = 10
        paper.venue = "NeurIPS"
        paper.research_domains = ["ML"]
        paper.authors = []
        paper.technologies = []
        paper.datasets = []
        paper.methodologies = []

        author = MagicMock()
        author.name = "Alice"
        author.affiliated_institutions = []

        mock_graph = MagicMock()
        mock_graph.institutions = {"MIT": inst}
        mock_graph.papers = {"p1": paper}
        mock_graph.authors = {"Alice": author}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        result = service.list_profiles(uuid.uuid4())
        assert len(result) == 1
        profile = result[0]
        assert profile.name == "MIT"
        assert profile.type == "university"
        assert profile.total_papers == 1
        assert profile.total_authors == 1
        assert profile.total_citations == 10
        assert len(profile.research_domains) == 1
        assert profile.research_domains[0].name == "ML"


class TestServiceGetProfile:
    def test_raises_404_for_missing(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {}
        mock_graph_service.get_raw_graph.return_value = mock_graph

        with pytest.raises(HTTPException) as exc:
            service.get_profile(uuid.uuid4(), "Nonexistent")
        assert exc.value.status_code == 404

    def test_returns_profile(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        inst = MagicMock()
        inst.name = "Google"
        inst.type.value = "company"
        inst.paper_ids = []
        inst.author_names = []

        mock_graph = MagicMock()
        mock_graph.institutions = {"Google": inst}
        mock_graph.papers = {}
        mock_graph.authors = {}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        profile = service.get_profile(uuid.uuid4(), "Google")
        assert profile.name == "Google"
        assert profile.type == "company"


class TestServiceCompare:
    def test_raises_error_for_single_institution(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        with pytest.raises(HTTPException) as exc:
            service.compare(uuid.uuid4(), ["MIT"])
        assert exc.value.status_code == 400

    def test_raises_error_for_too_many(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        with pytest.raises(HTTPException) as exc:
            service.compare(uuid.uuid4(), ["A", "B", "C", "D", "E", "F"])
        assert exc.value.status_code == 400

    def test_raises_404_for_missing(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {"MIT": MagicMock()}
        mock_graph_service.get_raw_graph.return_value = mock_graph

        with pytest.raises(HTTPException) as exc:
            service.compare(uuid.uuid4(), ["MIT", "Nonexistent"])
        assert exc.value.status_code == 404

    def test_returns_comparison(
        self, service: InstitutionProfileService, mock_graph_service: MagicMock
    ) -> None:
        inst1 = MagicMock()
        inst1.name = "MIT"
        inst1.type.value = "university"
        inst1.paper_ids = []
        inst1.author_names = []

        inst2 = MagicMock()
        inst2.name = "Stanford"
        inst2.type.value = "university"
        inst2.paper_ids = []
        inst2.author_names = []

        mock_graph = MagicMock()
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}
        mock_graph.papers = {}
        mock_graph.authors = {}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        result = service.compare(uuid.uuid4(), ["MIT", "Stanford"])
        assert len(result) == 2
        assert result[0].name == "MIT"
        assert result[1].name == "Stanford"


# =============================================================================
# Route tests — via TestClient with mocked dependencies
# =============================================================================


@pytest.fixture
def inv_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_profile() -> InstitutionProfile:
    return InstitutionProfile(
        name="MIT",
        type="university",
        total_papers=10,
        total_authors=5,
        total_citations=100,
        research_domains=[EntityCount(name="ML", count=8)],
        technologies=[EntityCount(name="PyTorch", count=6)],
        datasets=[EntityCount(name="ImageNet", count=4)],
        methodologies=[EntityCount(name="CNN", count=5)],
        top_authors=[AuthorEntry(name="Alice", paper_count=8)],
        top_papers=[PaperEntry(id="p1", title="Paper 1", year=2024)],
        yearly_trends=[YearlyTrend(year=2024, paper_count=10)],
        collaborating_institutions=[
            CollaborationEntry(institution_name="Stanford", joint_paper_count=3)
        ],
        co_authors=[AuthorEntry(name="Bob", paper_count=2)],
    )


def _override_deps(
    app: FastAPI,
    svc: MagicMock,
) -> None:
    app.dependency_overrides[get_institution_profile_service] = lambda: svc


class TestListInstitutionProfiles:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
        sample_profile: InstitutionProfile,
    ) -> None:
        mock_service.list_profiles.return_value = [sample_profile]
        _override_deps(test_app, mock_service)

        resp = client.get(f"/investigations/{inv_id}/institution-profiles")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 1
        assert body[0]["name"] == "MIT"
        assert body[0]["total_papers"] == 10
        assert body[0]["total_citations"] == 100
        assert body[0]["research_domains"][0]["name"] == "ML"
        assert body[0]["technologies"][0]["name"] == "PyTorch"
        assert body[0]["datasets"][0]["name"] == "ImageNet"
        assert body[0]["methodologies"][0]["name"] == "CNN"
        assert body[0]["top_authors"][0]["name"] == "Alice"
        assert body[0]["top_papers"][0]["title"] == "Paper 1"
        assert body[0]["yearly_trends"][0]["year"] == 2024
        assert body[0]["collaborating_institutions"][0]["institution_name"] == "Stanford"
        assert body[0]["co_authors"][0]["name"] == "Bob"

    def test_empty(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
    ) -> None:
        mock_service.list_profiles.return_value = []
        _override_deps(test_app, mock_service)

        resp = client.get(f"/investigations/{inv_id}/institution-profiles")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []


class TestGetInstitutionProfile:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
        sample_profile: InstitutionProfile,
    ) -> None:
        mock_service.get_profile.return_value = sample_profile
        _override_deps(test_app, mock_service)

        resp = client.get(f"/investigations/{inv_id}/institution-profiles/MIT")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["name"] == "MIT"
        assert body["total_papers"] == 10

    def test_404(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
    ) -> None:
        mock_service.get_profile.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        _override_deps(test_app, mock_service)

        resp = client.get(f"/investigations/{inv_id}/institution-profiles/Nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestCompareInstitutions:
    def test_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
        sample_profile: InstitutionProfile,
    ) -> None:
        mock_service.compare.return_value = [sample_profile, sample_profile]
        _override_deps(test_app, mock_service)

        resp = client.post(
            f"/investigations/{inv_id}/institution-profiles/compare",
            json={"institution_names": ["MIT", "Stanford"]},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 2
        assert body[0]["name"] == "MIT"

    def test_400_when_too_few(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
    ) -> None:
        mock_service.compare.side_effect = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        _override_deps(test_app, mock_service)

        resp = client.post(
            f"/investigations/{inv_id}/institution-profiles/compare",
            json={"institution_names": ["MIT"]},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_404_if_any_missing(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_service: MagicMock,
    ) -> None:
        mock_service.compare.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        _override_deps(test_app, mock_service)

        resp = client.post(
            f"/investigations/{inv_id}/institution-profiles/compare",
            json={"institution_names": ["MIT", "Nonexistent"]},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
