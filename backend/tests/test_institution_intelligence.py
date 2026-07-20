"""Tests for Institution Intelligence — search, ranking, trends, and comparison services + routes."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.v1 import v1_router
from app.modules.institution.api.dependencies import (
    get_institution_analytics_service,
    get_institution_comparison_service,
    get_institution_search_service,
)
from app.modules.institution.api.schemas import (
    CompareV2Request,
    FilterRequest,
    InstitutionComparisonDetailResponse,
    InstitutionIntelligenceResponse,
    InstitutionRankingEntryResponse,
    InstitutionSearchResultResponse,
    InstitutionTrendResponse,
    TopicSearchResultResponse,
    YearlyTrendResponse,
)
from app.modules.institution.domain.models import (
    AuthorEntry,
    EntityCount,
    InstitutionComparisonDetail,
    InstitutionIntelligence,
    InstitutionRankingEntry,
    InstitutionSearchResult,
    InstitutionTrend,
    PaperEntry,
    TopicSearchResult,
    YearlyTrend,
)
from app.modules.institution.service.comparison import (
    InstitutionComparisonService,
)
from app.modules.institution.service.ranking import (
    InstitutionAnalyticsService,
)
from app.modules.institution.service.search import (
    InstitutionSearchService,
)

# =============================================================================
# Search domain model + schema tests
# =============================================================================


class TestSearchDomainModels:
    def test_institution_search_result(self) -> None:
        r = InstitutionSearchResult(
            name="MIT",
            type="university",
            paper_count=10,
            author_count=5,
            citation_count=100,
            relevance_score=0.95,
        )
        assert r.name == "MIT"
        assert r.relevance_score == 0.95

    def test_topic_search_result(self) -> None:
        r = TopicSearchResult(
            institution_name="Stanford",
            paper_count=5,
            citation_count=50,
            top_papers=[PaperEntry(id="p1", title="Paper")],
            top_authors=[AuthorEntry(name="Alice", paper_count=3)],
            relevance_score=0.8,
        )
        assert r.institution_name == "Stanford"
        assert r.top_papers[0].title == "Paper"
        assert r.top_authors[0].name == "Alice"


class TestSearchSchemas:
    def test_institution_search_result_response(self) -> None:
        r = InstitutionSearchResultResponse(
            name="MIT",
            type="university",
            paper_count=10,
            author_count=5,
            citation_count=100,
            relevance_score=0.95,
        )
        assert r.name == "MIT"

    def test_topic_search_result_response(self) -> None:
        r = TopicSearchResultResponse(
            institution_name="Stanford",
            paper_count=5,
            citation_count=50,
        )
        assert r.institution_name == "Stanford"

    def test_filter_request(self) -> None:
        r = FilterRequest(
            research_domains=["ML"],
            min_year=2020,
            min_papers=5,
        )
        assert r.research_domains == ["ML"]
        assert r.min_year == 2020

    def test_institution_ranking_entry_response(self) -> None:
        r = InstitutionRankingEntryResponse(
            name="MIT",
            type="university",
            paper_count=10,
            citation_count=100,
            avg_citations=10.0,
            growth_rate=0.5,
            technology_diversity=5,
            research_diversity=3,
            collaboration_score=0.8,
            rank=1,
        )
        assert r.name == "MIT"
        assert r.rank == 1

    def test_institution_intelligence_response(self) -> None:
        r = InstitutionIntelligenceResponse(
            top_institutions=[
                InstitutionRankingEntryResponse(
                    name="MIT",
                    type="university",
                    paper_count=10,
                    citation_count=100,
                    avg_citations=10.0,
                    growth_rate=0.5,
                    technology_diversity=5,
                    research_diversity=3,
                    collaboration_score=0.8,
                    rank=1,
                )
            ],
        )
        assert len(r.top_institutions) == 1

    def test_institution_trend_response(self) -> None:
        r = InstitutionTrendResponse(
            name="MIT",
            yearly_publications=[YearlyTrendResponse(year=2024, paper_count=5)],
            growth_rate=0.5,
            is_emerging=True,
        )
        assert r.name == "MIT"
        assert r.is_emerging

    def test_compare_v2_request(self) -> None:
        r = CompareV2Request(institution_names=["MIT", "Stanford"])
        assert len(r.institution_names) == 2

    def test_institution_comparison_detail_response(self) -> None:
        r = InstitutionComparisonDetailResponse(
            name="MIT",
            type="university",
            total_papers=10,
            total_citations=100,
            total_authors=5,
            avg_citations=10.0,
            growth_rate=0.5,
            research_diversity_score=0.3,
            collaboration_score=0.8,
        )
        assert r.name == "MIT"
        assert r.strengths == []


# =============================================================================
# InstitutionSearchService tests
# =============================================================================


@pytest.fixture
def mock_graph_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def search_service(mock_graph_service: MagicMock) -> InstitutionSearchService:
    return InstitutionSearchService(mock_graph_service)


def _make_mock_institution(
    name: str, type_val: str, paper_ids: list[str], author_names: list[str]
) -> MagicMock:
    node = MagicMock()
    node.name = name
    node.type.value = type_val
    node.paper_ids = paper_ids
    node.author_names = author_names
    return node


def _make_mock_paper(
    pid: str,
    title: str,
    year: int = 2024,
    citation_count: int = 0,
    research_domains: list[str] | None = None,
    technologies: list | None = None,
    datasets: list | None = None,
    methodologies: list | None = None,
    authors: list | None = None,
) -> MagicMock:
    paper = MagicMock()
    paper.id = pid
    paper.title = title
    paper.year = year
    paper.citation_count = citation_count
    paper.research_domains = research_domains or []
    paper.technologies = technologies or []
    paper.datasets = datasets or []
    paper.methodologies = methodologies or []
    paper.authors = authors or []
    return paper


class TestSearchService:
    def test_search_empty_query(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        result = search_service.search(uuid.uuid4(), "")
        assert result == []

    def test_search_returns_ranked_results(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {
            "Massachusetts Institute of Technology": _make_mock_institution(
                "Massachusetts Institute of Technology",
                "university",
                ["p1", "p2"],
                ["A", "B"],
            ),
            "Stanford University": _make_mock_institution(
                "Stanford University",
                "university",
                ["p3"],
                ["C"],
            ),
        }
        paper1 = _make_mock_paper("p1", "Paper 1", citation_count=10)
        paper2 = _make_mock_paper("p2", "Paper 2", citation_count=5)
        paper3 = _make_mock_paper("p3", "Paper 3", citation_count=3)
        mock_graph.papers = {"p1": paper1, "p2": paper2, "p3": paper3}
        mock_graph.services.centrality = None
        mock_graph.institutions["Massachusetts Institute of Technology"].paper_ids = ["p1", "p2"]
        mock_graph.institutions["Stanford University"].paper_ids = ["p3"]
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = search_service.search(uuid.uuid4(), "MIT")
        assert len(results) > 0
        assert results[0].name == "Massachusetts Institute of Technology"

    def test_search_fuzzy_matching(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {
            "MIT": _make_mock_institution("MIT", "university", ["p1"], ["A"]),
            "CMU": _make_mock_institution("CMU", "university", ["p2"], ["B"]),
        }
        paper1 = _make_mock_paper("p1", "Paper 1")
        paper2 = _make_mock_paper("p2", "Paper 2")
        mock_graph.papers = {"p1": paper1, "p2": paper2}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = search_service.search(uuid.uuid4(), "M")
        names = [r.name for r in results]
        assert "MIT" in names
        assert "CMU" not in names

    def test_topic_search(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1"], ["A"])
        inst2 = _make_mock_institution("Stanford", "university", ["p2"], ["B"])
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}
        mock_graph.authors = {}

        author1 = MagicMock()
        author1.name = "Alice"
        author2 = MagicMock()
        author2.name = "Bob"

        tech1 = MagicMock()
        tech1.name = "PyTorch"

        paper1 = _make_mock_paper(
            "p1", "Paper 1", research_domains=["Machine Learning"], authors=[author1]
        )
        paper1.institutions = [inst1]
        paper1.technologies = [tech1]
        paper2 = _make_mock_paper(
            "p2", "Paper 2", research_domains=["Computer Vision"], authors=[author2]
        )
        paper2.institutions = [inst2]

        mock_graph.papers = {"p1": paper1, "p2": paper2}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = search_service.topic_search(uuid.uuid4(), "Machine Learning")
        assert len(results) >= 1
        assert results[0].institution_name == "MIT"

    def test_topic_search_empty_query(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        result = search_service.topic_search(uuid.uuid4(), "")
        assert result == []

    def test_filter_institutions(
        self, search_service: InstitutionSearchService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1"], ["A"])
        mock_graph.institutions = {"MIT": inst1}
        mock_graph.authors = {}

        tech1 = MagicMock()
        tech1.name = "PyTorch"

        paper1 = _make_mock_paper(
            "p1",
            "Paper 1",
            year=2023,
            citation_count=20,
            technologies=[tech1],
            research_domains=["ML"],
        )
        paper1.institutions = [inst1]
        mock_graph.papers = {"p1": paper1}
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = search_service.filter_institutions(
            uuid.uuid4(),
            technologies=["PyTorch"],
            min_year=2020,
        )
        assert len(results) == 1
        assert results[0].name == "MIT"

        results = search_service.filter_institutions(
            uuid.uuid4(),
            methodologies=["CNN"],
        )
        assert len(results) == 0


# =============================================================================
# InstitutionAnalyticsService tests
# =============================================================================


@pytest.fixture
def analytics_service(mock_graph_service: MagicMock) -> InstitutionAnalyticsService:
    return InstitutionAnalyticsService(mock_graph_service)


class TestAnalyticsService:
    def test_rank_publication_count(
        self, analytics_service: InstitutionAnalyticsService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1", "p2"], ["A"])
        inst2 = _make_mock_institution("Stanford", "university", ["p3"], ["B"])
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}

        p1 = _make_mock_paper("p1", "P1", year=2024, citation_count=10)
        p2 = _make_mock_paper("p2", "P2", year=2023, citation_count=5)
        p3 = _make_mock_paper("p3", "P3", year=2024, citation_count=3)
        mock_graph.papers = {"p1": p1, "p2": p2, "p3": p3}
        mock_graph.years = [2023, 2024]

        centrality = MagicMock()
        centrality.degree_centrality.return_value = {"MIT": 0.8, "Stanford": 0.3}
        mock_graph.services.centrality = centrality
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = analytics_service.rank(uuid.uuid4(), "publication_count", limit=5)
        assert len(results) == 2
        assert results[0].name == "MIT"
        assert results[0].rank == 1
        assert results[1].name == "Stanford"

    def test_rank_citation_count(
        self, analytics_service: InstitutionAnalyticsService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1", "p2"], ["A"])
        inst2 = _make_mock_institution("Stanford", "university", ["p3"], ["B"])
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}

        p1 = _make_mock_paper("p1", "P1", citation_count=100)
        p2 = _make_mock_paper("p2", "P2", citation_count=50)
        p3 = _make_mock_paper("p3", "P3", citation_count=200)
        mock_graph.papers = {"p1": p1, "p2": p2, "p3": p3}
        mock_graph.years = [2024]

        centrality = MagicMock()
        centrality.degree_centrality.return_value = {}
        mock_graph.services.centrality = centrality
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = analytics_service.rank(uuid.uuid4(), "citation_count", limit=5)
        assert len(results) == 2
        assert results[0].name == "Stanford"
        assert results[0].citation_count == 200

    def test_get_intelligence(
        self, analytics_service: InstitutionAnalyticsService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1", "p2", "p3"], ["A"])
        mock_graph.institutions = {"MIT": inst1}
        p1 = _make_mock_paper("p1", "P1", year=2024)
        p2 = _make_mock_paper("p2", "P2", year=2023)
        p3 = _make_mock_paper("p3", "P3", year=2022)
        mock_graph.papers = {"p1": p1, "p2": p2, "p3": p3}
        mock_graph.years = [2022, 2023, 2024]

        centrality = MagicMock()
        centrality.degree_centrality.return_value = {"MIT": 0.5}
        mock_graph.services.centrality = centrality
        mock_graph_service.get_raw_graph.return_value = mock_graph

        result = analytics_service.get_intelligence(uuid.uuid4())
        assert len(result.top_institutions) == 1
        assert result.top_institutions[0].name == "MIT"

    def test_get_intelligence_empty(
        self, analytics_service: InstitutionAnalyticsService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {}
        mock_graph_service.get_raw_graph.return_value = mock_graph
        result = analytics_service.get_intelligence(uuid.uuid4())
        assert result.top_institutions == []
        assert result.emerging_institutions == []

    def test_get_trends(
        self, analytics_service: InstitutionAnalyticsService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1", "p2", "p3"], ["A"])
        mock_graph.institutions = {"MIT": inst1}
        p1 = _make_mock_paper(
            "p1",
            "P1",
            year=2023,
            citation_count=5,
            technologies=[MagicMock()],
            research_domains=["ML"],
        )
        p1.technologies[0].name = "PyTorch"
        p2 = _make_mock_paper(
            "p2",
            "P2",
            year=2024,
            citation_count=10,
            technologies=[MagicMock()],
            research_domains=["ML"],
        )
        p2.technologies[0].name = "PyTorch"
        p3 = _make_mock_paper(
            "p3",
            "P3",
            year=2024,
            citation_count=8,
            technologies=[MagicMock()],
            research_domains=["ML"],
        )
        p3.technologies[0].name = "TensorFlow"
        mock_graph.papers = {"p1": p1, "p2": p2, "p3": p3}
        mock_graph.years = [2023, 2024]
        mock_graph.services.centrality = None
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = analytics_service.get_trends(uuid.uuid4(), ["MIT"])
        assert len(results) == 1
        assert results[0].name == "MIT"
        assert len(results[0].yearly_publications) == 2
        assert results[0].growth_rate > 0
        assert len(results[0].technology_adoption) == 2


# =============================================================================
# InstitutionComparisonService tests
# =============================================================================


@pytest.fixture
def comparison_service(mock_graph_service: MagicMock) -> InstitutionComparisonService:
    return InstitutionComparisonService(mock_graph_service)


class TestComparisonService:
    def test_raises_error_for_single(
        self, comparison_service: InstitutionComparisonService, mock_graph_service: MagicMock
    ) -> None:
        with pytest.raises(HTTPException) as exc:
            comparison_service.compare(uuid.uuid4(), ["MIT"])
        assert exc.value.status_code == 400

    def test_raises_error_for_too_many(
        self, comparison_service: InstitutionComparisonService, mock_graph_service: MagicMock
    ) -> None:
        with pytest.raises(HTTPException) as exc:
            comparison_service.compare(uuid.uuid4(), ["A", "B", "C", "D", "E", "F"])
        assert exc.value.status_code == 400

    def test_raises_404_for_missing(
        self, comparison_service: InstitutionComparisonService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        mock_graph.institutions = {"MIT": _make_mock_institution("MIT", "university", [], [])}
        mock_graph_service.get_raw_graph.return_value = mock_graph
        with pytest.raises(HTTPException) as exc:
            comparison_service.compare(uuid.uuid4(), ["MIT", "Nonexistent"])
        assert exc.value.status_code == 404

    def test_compare_returns_details(
        self, comparison_service: InstitutionComparisonService, mock_graph_service: MagicMock
    ) -> None:
        mock_graph = MagicMock()
        inst1 = _make_mock_institution("MIT", "university", ["p1"], ["Alice"])
        inst2 = _make_mock_institution("Stanford", "university", ["p2"], ["Bob"])
        mock_graph.institutions = {"MIT": inst1, "Stanford": inst2}

        p1 = _make_mock_paper(
            "p1",
            "Paper 1",
            year=2024,
            citation_count=50,
            research_domains=["ML"],
            technologies=[MagicMock()],
        )
        p1.technologies[0].name = "PyTorch"
        p1.institutions = [inst1]

        p2 = _make_mock_paper(
            "p2",
            "Paper 2",
            year=2024,
            citation_count=30,
            research_domains=["CV"],
            technologies=[MagicMock()],
        )
        p2.technologies[0].name = "TensorFlow"
        p2.institutions = [inst2]

        mock_graph.papers = {"p1": p1, "p2": p2}
        mock_graph.years = [2024]
        centrality = MagicMock()
        centrality.degree_centrality.return_value = {"MIT": 0.5, "Stanford": 0.3}
        centrality.collaboration_edges.return_value = []
        mock_graph.services.centrality = centrality
        mock_graph_service.get_raw_graph.return_value = mock_graph

        results = comparison_service.compare(uuid.uuid4(), ["MIT", "Stanford"])
        assert len(results) == 2
        assert results[0].name == "MIT"
        assert results[1].name == "Stanford"
        assert results[0].total_papers == 1
        assert results[0].total_citations == 50


# =============================================================================
# Route tests — via TestClient with mocked dependencies
# =============================================================================


@pytest.fixture
def inv_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_search_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_analytics_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_comparison_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


def _override_search(app: FastAPI, svc: MagicMock) -> None:
    app.dependency_overrides[get_institution_search_service] = lambda: svc


def _override_analytics(app: FastAPI, svc: MagicMock) -> None:
    app.dependency_overrides[get_institution_analytics_service] = lambda: svc


def _override_comparison(app: FastAPI, svc: MagicMock) -> None:
    app.dependency_overrides[get_institution_comparison_service] = lambda: svc


class TestSearchRoutes:
    def test_search_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_search_service: MagicMock,
    ) -> None:
        mock_search_service.search.return_value = [
            InstitutionSearchResult(
                name="MIT",
                type="university",
                paper_count=10,
                author_count=5,
                citation_count=100,
                relevance_score=0.95,
            ),
        ]
        _override_search(test_app, mock_search_service)
        resp = client.get(f"/investigations/{inv_id}/institutions/search", params={"q": "MIT"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 1
        assert body[0]["name"] == "MIT"
        assert body[0]["relevance_score"] == 0.95

    def test_search_empty(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_search_service: MagicMock,
    ) -> None:
        mock_search_service.search.return_value = []
        _override_search(test_app, mock_search_service)
        resp = client.get(
            f"/investigations/{inv_id}/institutions/search", params={"q": "Nonexistent"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_search_missing_query(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_search_service: MagicMock,
    ) -> None:
        _override_search(test_app, mock_search_service)
        resp = client.get(f"/investigations/{inv_id}/institutions/search")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_topic_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_search_service: MagicMock,
    ) -> None:
        mock_search_service.topic_search.return_value = [
            TopicSearchResult(
                institution_name="MIT",
                paper_count=5,
                citation_count=50,
                top_papers=[PaperEntry(id="p1", title="Paper")],
                top_authors=[AuthorEntry(name="Alice", paper_count=3)],
                relevance_score=0.8,
            ),
        ]
        _override_search(test_app, mock_search_service)
        resp = client.get(
            f"/investigations/{inv_id}/institutions/topic", params={"q": "Machine Learning"}
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 1
        assert body[0]["institution_name"] == "MIT"
        assert body[0]["top_papers"][0]["title"] == "Paper"
        assert body[0]["top_authors"][0]["name"] == "Alice"

    def test_filter_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_search_service: MagicMock,
    ) -> None:
        mock_search_service.filter_institutions.return_value = [
            InstitutionSearchResult(
                name="MIT",
                type="university",
                paper_count=5,
                author_count=3,
                citation_count=50,
                relevance_score=1.0,
            ),
        ]
        _override_search(test_app, mock_search_service)
        resp = client.post(
            f"/investigations/{inv_id}/institutions/filter",
            json={"research_domains": ["ML"], "min_year": 2020},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()[0]["name"] == "MIT"


class TestRankingRoutes:
    def test_ranking_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_analytics_service: MagicMock,
    ) -> None:
        mock_analytics_service.rank.return_value = [
            InstitutionRankingEntry(
                name="MIT",
                type="university",
                paper_count=10,
                citation_count=100,
                avg_citations=10.0,
                growth_rate=0.5,
                technology_diversity=5,
                research_diversity=3,
                collaboration_score=0.8,
                rank=1,
            ),
        ]
        _override_analytics(test_app, mock_analytics_service)
        resp = client.get(
            f"/investigations/{inv_id}/institutions/ranking",
            params={"by": "publication_count", "limit": 5},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 1
        assert body[0]["name"] == "MIT"
        assert body[0]["rank"] == 1

    def test_intelligence_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_analytics_service: MagicMock,
    ) -> None:
        entry = InstitutionRankingEntry(
            name="MIT",
            type="university",
            paper_count=10,
            citation_count=100,
            avg_citations=10.0,
            growth_rate=0.5,
            technology_diversity=5,
            research_diversity=3,
            collaboration_score=0.8,
            rank=1,
        )
        mock_analytics_service.get_intelligence.return_value = InstitutionIntelligence(
            top_institutions=[entry],
            emerging_institutions=[entry],
        )
        _override_analytics(test_app, mock_analytics_service)
        resp = client.get(f"/investigations/{inv_id}/institutions/intelligence")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body["top_institutions"]) == 1
        assert len(body["emerging_institutions"]) == 1

    def test_trends_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_analytics_service: MagicMock,
    ) -> None:
        mock_analytics_service.get_trends.return_value = [
            InstitutionTrend(
                name="MIT",
                yearly_publications=[YearlyTrend(year=2024, paper_count=5)],
                growth_rate=0.5,
                is_emerging=True,
                technology_adoption=[EntityCount(name="PyTorch", count=3)],
                research_evolution=[EntityCount(name="ML", count=5)],
            ),
        ]
        _override_analytics(test_app, mock_analytics_service)
        resp = client.get(
            f"/investigations/{inv_id}/institutions/trends",
            params={"names": "MIT"},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 1
        assert body[0]["name"] == "MIT"
        assert body[0]["is_emerging"] is True


class TestComparisonV2Routes:
    def test_compare_v2_success(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_comparison_service: MagicMock,
    ) -> None:
        mock_comparison_service.compare.return_value = [
            InstitutionComparisonDetail(
                name="MIT",
                type="university",
                total_papers=10,
                total_citations=100,
                total_authors=5,
                avg_citations=10.0,
                growth_rate=0.5,
                research_diversity_score=0.3,
                collaboration_score=0.8,
                strengths=["High publication output"],
                weaknesses=["Declining publication trend"],
            ),
            InstitutionComparisonDetail(
                name="Stanford",
                type="university",
                total_papers=8,
                total_citations=80,
                total_authors=4,
                avg_citations=10.0,
                growth_rate=0.3,
                research_diversity_score=0.4,
                collaboration_score=0.6,
            ),
        ]
        _override_comparison(test_app, mock_comparison_service)
        resp = client.post(
            f"/investigations/{inv_id}/institutions/compare-v2",
            json={"institution_names": ["MIT", "Stanford"]},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body) == 2
        assert body[0]["name"] == "MIT"
        assert "High publication output" in body[0]["strengths"]

    def test_compare_v2_400(
        self,
        test_app: FastAPI,
        client: TestClient,
        inv_id: uuid.UUID,
        mock_comparison_service: MagicMock,
    ) -> None:
        mock_comparison_service.compare.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
        )
        _override_comparison(test_app, mock_comparison_service)
        resp = client.post(
            f"/investigations/{inv_id}/institutions/compare-v2",
            json={"institution_names": ["MIT"]},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
