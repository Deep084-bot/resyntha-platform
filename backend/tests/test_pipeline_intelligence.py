"""Tests for the IntelligenceStage pipeline integration.

All tests use mocked dependencies — no database, no LLM, no real graph.
Focus is on orchestration, error handling, metrics, and artifact creation.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from app.modules.artifact.domain.models import Artifact, ArtifactStatus, ArtifactType
from app.modules.artifact.schemas.request import CreateArtifactRequest
from app.modules.artifact.schemas.response import ArtifactResponse
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.intelligence.aggregation.models import (
    LandscapeResult,
    Observation,
    OverviewSection,
)
from app.modules.intelligence.api.models import LandscapeResponse
from app.modules.intelligence.graph.builder import PaperMetadata
from app.modules.intelligence.graph.models import ResearchGraph
from app.modules.paper.domain.models import Paper
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stages.intelligence import IntelligenceStage


# =============================================================================
# Helpers
# =============================================================================


def _make_paper(pid: uuid.UUID, year: int = 2023) -> Paper:
    return Paper(
        id=pid,
        title=f"Paper {pid}",
        authors=["Alice", "Bob"],
        year=year,
        citation_count=5,
        venue="Test Venue",
        doi=f"10.1234/{pid}",
    )


def _make_knowledge(
    paper_id: uuid.UUID,
    inv_id: uuid.UUID,
    methodology: str = "CNN",
) -> ExtractedKnowledge:
    return ExtractedKnowledge(
        id=uuid.uuid4(),
        investigation_id=inv_id,
        paper_id=paper_id,
        paper_title=f"Paper {paper_id}",
        methodology=methodology,
        key_findings=["finding1"],
        limitations=["limitation1"],
        future_work=["future1"],
        relevant_techniques=["conv"],
        cited_works=["ref1"],
        key_contributions=["contrib1"],
        research_questions=["q1"],
        summary="Test summary",
        model_used="test-model",
    )


def _context(
    inv_id: uuid.UUID | None = None,
    exec_id: uuid.UUID | None = None,
) -> PipelineContext:
    ctx = PipelineContext(
        investigation_id=inv_id or uuid.uuid4(),
        execution_id=exec_id or uuid.uuid4(),
    )
    ctx.add_artifact("extracted_knowledge_ids", [str(uuid.uuid4())])
    ctx.set_metadata("query", "test query")
    return ctx


# =============================================================================
# Mock types
# =============================================================================


@dataclass
class MockArtifactService:
    created: list[CreateArtifactRequest] = field(default_factory=list)

    def create_artifact(
        self,
        investigation_id: uuid.UUID,
        request: CreateArtifactRequest,
        status: ArtifactStatus = ArtifactStatus.PENDING,
    ) -> ArtifactResponse:
        self.created.append(request)
        return ArtifactResponse(
            id=uuid.uuid4(),
            investigation_id=investigation_id,
            execution_id=request.execution_id,
            artifact_type=request.artifact_type,
            version=request.version,
            status=status,
            payload=request.payload,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


def _execute(stage: IntelligenceStage, ctx: PipelineContext) -> PipelineResult:
    """Synchronously run the async IntelligenceStage."""
    return asyncio.run(stage.execute(ctx))


@dataclass
class MockExtractionRepo:
    records: list[ExtractedKnowledge] = field(default_factory=list)

    def list_by_investigation(self, inv_id: uuid.UUID) -> list[ExtractedKnowledge]:
        return self.records


@dataclass
class MockPaperRepo:
    papers: list[Paper] = field(default_factory=list)

    def list_by_investigation(self, inv_id: uuid.UUID) -> list[Paper]:
        return self.papers


@dataclass
class MockGraphBuilder:
    return_graph: ResearchGraph = field(default_factory=ResearchGraph)
    last_records: list = field(default_factory=list)
    last_paper_map: dict | None = None

    def build(self, records, paper_map=None):
        self.last_records = records
        self.last_paper_map = paper_map
        return self.return_graph


@dataclass
class FailingMockGraphBuilder:
    def build(self, records, paper_map=None):
        raise RuntimeError("Graph build failed")


@dataclass
class FailingMockEngine:
    def run(self):
        raise RuntimeError("Analyzer failed")


# =============================================================================
# Tests
# =============================================================================


class TestIntelligenceStage:
    def test_construct_with_all_deps(self) -> None:
        """Stage can be constructed with all required dependencies."""
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(),
            paper_repository=MockPaperRepo(),
            artifact_service=MockArtifactService(),
        )
        assert stage.name() == "intelligence"
        assert "extracted_knowledge_ids" in stage.consumes
        assert "intelligence_landscape" in stage.produces

    def test_empty_no_records_returns_success(self) -> None:
        """No extracted knowledge → early SUCCESS with zero metrics."""
        ctx = _context()
        mock_artifact = MockArtifactService()
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(),
            paper_repository=MockPaperRepo(),
            artifact_service=mock_artifact,
        )
        result = _execute(stage, ctx)
        assert result == PipelineResult.SUCCESS
        assert ctx.metrics.get("intelligence_papers") == 0
        assert ctx.metrics.get("total_intelligence_duration") is not None
        # No artifacts created for empty results
        assert len(mock_artifact.created) == 0

    def test_single_paper_produces_artifacts(self) -> None:
        """Investigation with papers creates 2 RESEARCH_LANDSCAPE artifacts."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        mock_artifact = MockArtifactService()

        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=mock_artifact,
        )

        result = _execute(stage, ctx)

        assert result == PipelineResult.SUCCESS
        assert len(mock_artifact.created) == 2

        # Verify artifact types
        for req in mock_artifact.created:
            assert req.artifact_type == ArtifactType.RESEARCH_LANDSCAPE
            assert req.execution_id == ctx.execution_id
            assert req.payload["investigation_id"] == str(inv_id)

        # Verify formats
        formats = {req.payload["format"] for req in mock_artifact.created}
        assert formats == {"markdown", "json"}

    def test_context_artifacts_stored(self) -> None:
        """Markdown, JSON, and LandscapeResponse are stored in context."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)

        assert ctx.get_artifact("intelligence_markdown") is not None
        assert ctx.get_artifact("intelligence_json") is not None
        assert ctx.get_artifact("intelligence_landscape") is not None
        assert isinstance(ctx.get_artifact("intelligence_markdown"), str)
        assert isinstance(ctx.get_artifact("intelligence_json"), dict)

    def test_landscape_response_type(self) -> None:
        """Context contains a LandscapeResponse, not a raw LandscapeResult."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)
        resp = ctx.get_artifact("intelligence_landscape")
        assert isinstance(resp, LandscapeResponse)

    def test_paper_map_built_correctly(self) -> None:
        """Paper metadata is passed to the graph builder."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid, year=2023)]
        graph_builder = MockGraphBuilder()

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
            graph_builder=graph_builder,
        )

        _execute(stage, ctx)

        paper_map = graph_builder.last_paper_map
        assert paper_map is not None
        assert str(pid) in paper_map
        meta = paper_map[str(pid)]
        assert isinstance(meta, PaperMetadata)
        assert meta.year == 2023
        assert meta.authors == ["Alice", "Bob"]

    def test_graph_failure_returns_failed(self) -> None:
        """When graph builder fails, stage returns FAILED, not crash."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
            graph_builder=FailingMockGraphBuilder(),
        )

        result = _execute(stage, ctx)
        assert result == PipelineResult.FAILED
        assert len(ctx.errors) == 1
        assert "intelligence" in ctx.errors[0]["stage"]

    def test_metrics_recorded(self) -> None:
        """All expected metrics are present after a successful run."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)

        expected_metrics = [
            "graph_build_duration",
            "analyzer_duration",
            "aggregation_duration",
            "presentation_duration",
            "total_intelligence_duration",
            "intelligence_papers",
            "entities_created",
            "authors",
            "institutions",
            "methodologies",
            "technologies",
            "intelligence_load_duration",
        ]
        for metric in expected_metrics:
            assert metric in ctx.metrics, f"Missing metric: {metric}"
            assert ctx.metrics[metric] is not None

    def test_logging_on_success(self, capsys) -> None:
        """Success path logs key events."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)

        captured = capsys.readouterr()
        assert "intelligence_started" in captured.out
        assert "graph_built" in captured.out
        assert "analysis_completed" in captured.out
        assert "presentation_completed" in captured.out
        assert "artifacts_created" in captured.out
        assert "intelligence_completed" in captured.out

    def test_logging_on_empty(self, capsys) -> None:
        """Empty investigation logs no_records, not an error."""
        ctx = _context()
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(),
            paper_repository=MockPaperRepo(),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)

        captured = capsys.readouterr()
        assert "intelligence_no_records" in captured.out
        assert "intelligence_started" in captured.out
        # No success logs for the full pipeline
        assert "intelligence_completed" not in captured.out

    def test_deterministic_output(self) -> None:
        """Same input produces identical artifacts, metrics, and context."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        # Use a fixed investigation ID to avoid uuid4 differences
        def run() -> tuple:
            ctx = _context(inv_id=inv_id)
            ma = MockArtifactService()
            stage = IntelligenceStage(
                extraction_repository=MockExtractionRepo(records=list(records)),
                paper_repository=MockPaperRepo(papers=list(papers)),
                artifact_service=ma,
            )
            _execute(stage, ctx)
            # Compare only the content, not artifact metadata (UUIDs, timestamps)
            md = ctx.get_artifact("intelligence_markdown")
            js = ctx.get_artifact("intelligence_json")
            metrics = {k: v for k, v in ctx.metrics.items() if k != "total_intelligence_duration"}
            return (md, str(js), tuple(sorted(metrics.items())))

        r1 = run()
        r2 = run()
        assert r1 == r2

    def test_entity_counts_metrics(self) -> None:
        """Metrics reflect actual entity counts from the graph."""
        inv_id = uuid.uuid4()
        pid1, pid2 = uuid.uuid4(), uuid.uuid4()
        records = [
            _make_knowledge(paper_id=pid1, inv_id=inv_id, methodology="CNN"),
            _make_knowledge(paper_id=pid2, inv_id=inv_id, methodology="RNN"),
        ]
        papers = [_make_paper(pid1), _make_paper(pid2)]

        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)

        assert ctx.metrics["intelligence_papers"] == 2
        assert ctx.metrics["entities_created"] >= 2
        assert ctx.metrics["methodologies"] >= 2

    def test_timeline_stage_independence(self) -> None:
        """IntelligenceStage doesn't interact with timeline — that's separate."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(
                records=[_make_knowledge(paper_id=pid, inv_id=inv_id)],
            ),
            paper_repository=MockPaperRepo(papers=[_make_paper(pid)]),
            artifact_service=MockArtifactService(),
        )

        _execute(stage, ctx)
        assert "timeline_recorded" not in ctx.artifacts


class TestIntelligenceStageConsumes:
    def test_requires_extracted_knowledge_ids(self) -> None:
        """Stage declares consumption of extracted_knowledge_ids."""
        assert "extracted_knowledge_ids" in IntelligenceStage.consumes

    def test_handles_no_extracted_knowledge_ids(self) -> None:
        """Stage works even if no extracted_knowledge_ids are in context."""
        ctx = PipelineContext(investigation_id=uuid.uuid4(), execution_id=uuid.uuid4())
        # Note: no extracted_knowledge_ids in artifacts
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(),
            paper_repository=MockPaperRepo(),
            artifact_service=MockArtifactService(),
        )
        result = _execute(stage, ctx)
        assert result == PipelineResult.SUCCESS


class TestIntelligenceStageArtifacts:
    def test_artifact_has_markdown_content(self) -> None:
        """Markdown artifact payload contains actual markdown content."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        ctx = _context(inv_id=inv_id)
        mock_artifact = MockArtifactService()

        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(
                records=[_make_knowledge(paper_id=pid, inv_id=inv_id)],
            ),
            paper_repository=MockPaperRepo(papers=[_make_paper(pid)]),
            artifact_service=mock_artifact,
        )

        _execute(stage, ctx)
        for req in mock_artifact.created:
            if req.payload["format"] == "markdown":
                assert isinstance(req.payload["content"], str)
                assert len(req.payload["content"]) > 50

    def test_artifact_has_json_content(self) -> None:
        """JSON artifact payload contains a dict with landscape data."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        ctx = _context(inv_id=inv_id)
        mock_artifact = MockArtifactService()

        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(
                records=[_make_knowledge(paper_id=pid, inv_id=inv_id)],
            ),
            paper_repository=MockPaperRepo(papers=[_make_paper(pid)]),
            artifact_service=mock_artifact,
        )

        _execute(stage, ctx)
        for req in mock_artifact.created:
            if req.payload["format"] == "json":
                assert isinstance(req.payload["content"], dict)
                assert "overview" in req.payload["content"]


class TestIntelligenceStageErrors:
    def test_error_does_not_crash_worker(self) -> None:
        """An exception during graph building returns FAILED, not raises."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(
                records=[_make_knowledge(paper_id=pid, inv_id=inv_id)],
            ),
            paper_repository=MockPaperRepo(papers=[_make_paper(pid)]),
            artifact_service=MockArtifactService(),
            graph_builder=FailingMockGraphBuilder(),
        )

        result = _execute(stage, ctx)
        assert result == PipelineResult.FAILED

    def test_error_still_records_duration(self) -> None:
        """Even on failure, total_intelligence_duration is recorded."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        ctx = _context(inv_id=inv_id)
        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(
                records=[_make_knowledge(paper_id=pid, inv_id=inv_id)],
            ),
            paper_repository=MockPaperRepo(papers=[_make_paper(pid)]),
            artifact_service=MockArtifactService(),
            graph_builder=FailingMockGraphBuilder(),
        )

        _execute(stage, ctx)
        assert "total_intelligence_duration" in ctx.metrics
        assert ctx.metrics["total_intelligence_duration"] >= 0


class TestIntelligenceStageIntegration:
    """Light integration — uses real aggregator, renderers, and service."""

    def test_end_to_end(self) -> None:
        """Full pipeline: data → graph → engine → aggregate → render → artifacts."""
        inv_id = uuid.uuid4()
        pid = uuid.uuid4()
        records = [_make_knowledge(paper_id=pid, inv_id=inv_id)]
        papers = [_make_paper(pid)]

        ctx = _context(inv_id=inv_id)
        mock_artifact = MockArtifactService()

        stage = IntelligenceStage(
            extraction_repository=MockExtractionRepo(records=records),
            paper_repository=MockPaperRepo(papers=papers),
            artifact_service=mock_artifact,
        )

        result = _execute(stage, ctx)
        assert result == PipelineResult.SUCCESS

        # Verify full output chain
        md = ctx.get_artifact("intelligence_markdown")
        js = ctx.get_artifact("intelligence_json")
        resp = ctx.get_artifact("intelligence_landscape")

        assert isinstance(md, str) and md.startswith("# Research Landscape")
        assert isinstance(js, dict) and "overview" in js
        assert isinstance(resp, LandscapeResponse)
        assert resp.overview.total_papers > 0

        # Verify 2 artifacts created
        assert len(mock_artifact.created) == 2

        # Verify metrics
        assert ctx.metrics["intelligence_papers"] == 1
        assert ctx.metrics["graph_build_duration"] >= 0
        assert ctx.metrics["analyzer_duration"] >= 0
        assert ctx.metrics["aggregation_duration"] >= 0
        assert ctx.metrics["presentation_duration"] >= 0
