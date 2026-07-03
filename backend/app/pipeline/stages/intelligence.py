"""IntelligenceStage — runs the full Intelligence pipeline after extraction.

Builds a ResearchGraph from ExtractedKnowledge, runs every registered
analyzer, aggregates the landscape, renders Markdown + JSON, and persists
artifacts.  Failures are isolated — never crash the worker.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.modules.artifact.domain.models import ArtifactStatus, ArtifactType
from app.modules.artifact.schemas.request import CreateArtifactRequest
from app.modules.artifact.service.service import ArtifactService
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.intelligence.aggregation import LandscapeAggregator
from app.modules.intelligence.analyzers import (
    BaseAnalyzer,
    CollaborationAnalyzer,
    DatasetAnalyzer,
    InstitutionAnalyzer,
    IntelligenceEngine,
    MethodologyAnalyzer,
    TechnologyAnalyzer,
    TemporalAnalyzer,
)
from app.modules.intelligence.api import IntelligenceService
from app.modules.intelligence.api.serializers import landscape_to_response
from app.modules.intelligence.config import IntelligenceConfig
from app.modules.intelligence.context import AnalysisContext
from app.modules.intelligence.graph.builder import PaperMetadata, ResearchGraphBuilder
from app.modules.intelligence.graph.models import ResearchGraph
from app.modules.intelligence.presentation import JsonRenderer, MarkdownRenderer
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger
from app.pipeline.context import PipelineContext
from app.pipeline.result import PipelineResult
from app.pipeline.stage import PipelineStage

logger = get_logger(__name__)

_ANALYZER_CLASSES: list[type[BaseAnalyzer]] = [
    InstitutionAnalyzer,
    MethodologyAnalyzer,
    TemporalAnalyzer,
    TechnologyAnalyzer,
    DatasetAnalyzer,
    CollaborationAnalyzer,
]


class IntelligenceStage(PipelineStage):
    """Build a ResearchGraph, run intelligence analyzers, aggregate,
    render, and persist artifacts.

    Consumes ``extracted_knowledge_ids`` (produced by ExtractStage).
    Produces ``intelligence_landscape``, ``intelligence_markdown``,
    and ``intelligence_json`` in the pipeline context.

    Failures inside this stage are logged and return FAILED — they
    never crash the worker.
    """

    consumes: list[str] = ["extracted_knowledge_ids"]
    produces: list[str] = [
        "intelligence_landscape",
        "intelligence_markdown",
        "intelligence_json",
    ]
    metadata: dict = {
        "description": "Run the full Intelligence pipeline after extraction",
    }

    def __init__(
        self,
        extraction_repository: ExtractionRepository,
        paper_repository: PaperRepository,
        artifact_service: ArtifactService,
        graph_builder: ResearchGraphBuilder | None = None,
        config: IntelligenceConfig | None = None,
        aggregator: LandscapeAggregator | None = None,
        markdown_renderer: MarkdownRenderer | None = None,
        json_renderer: JsonRenderer | None = None,
        service: IntelligenceService | None = None,
    ) -> None:
        self._extraction_repo = extraction_repository
        self._paper_repo = paper_repository
        self._graph_builder = graph_builder or ResearchGraphBuilder()
        self._config = config or IntelligenceConfig()
        self._aggregator = aggregator or LandscapeAggregator()
        self._md_renderer = markdown_renderer or MarkdownRenderer()
        self._json_renderer = json_renderer or JsonRenderer()
        self._service = service or IntelligenceService(
            aggregator=self._aggregator,
            markdown_renderer=self._md_renderer,
            json_renderer=self._json_renderer,
        )
        self._artifact_service = artifact_service

    def name(self) -> str:
        return "intelligence"

    async def execute(self, context: PipelineContext) -> PipelineResult:
        inv_id = context.investigation_id
        exec_id = context.execution_id
        inv_str = str(inv_id)

        logger.info("intelligence_started", investigation_id=inv_str)
        stage_start = datetime.now(UTC)

        try:
            # ── 1. Load data ──────────────────────────────────────
            t0 = datetime.now(UTC)
            records = self._extraction_repo.list_by_investigation(inv_id)
            papers = self._paper_repo.list_by_investigation(inv_id)
            t1 = datetime.now(UTC)
            load_duration = (t1 - t0).total_seconds()

            if not records:
                logger.info(
                    "intelligence_no_records",
                    investigation_id=inv_str,
                )
                context.record_metric("intelligence_papers", 0)
                context.record_metric("intelligence_load_duration", load_duration)
                context.record_metric("total_intelligence_duration", (datetime.now(UTC) - stage_start).total_seconds())
                return PipelineResult.SUCCESS

            # ── 2. Build paper_map ────────────────────────────────
            paper_map: dict[str, PaperMetadata] = {}
            for p in papers:
                paper_map[str(p.id)] = PaperMetadata(
                    year=p.year,
                    citation_count=p.citation_count,
                    venue=p.venue,
                    authors=p.authors,
                    doi=p.doi,
                )

            # ── 3. Build ResearchGraph ────────────────────────────
            t2 = datetime.now(UTC)
            graph = self._graph_builder.build(records, paper_map=paper_map)
            t3 = datetime.now(UTC)
            graph_duration = (t3 - t2).total_seconds()

            entity_count = (
                len(graph.papers) + len(graph.authors) + len(graph.institutions)
                + len(graph.methodologies) + len(graph.datasets)
                + len(graph.technologies)
            )

            logger.info(
                "graph_built",
                investigation_id=inv_str,
                duration_seconds=round(graph_duration, 3),
                papers=len(graph.papers),
                authors=len(graph.authors),
                institutions=len(graph.institutions),
                methodologies=len(graph.methodologies),
                datasets=len(graph.datasets),
                technologies=len(graph.technologies),
            )

            # ── 4. Run Intelligence Engine ────────────────────────
            t4 = datetime.now(UTC)
            analysis_context = AnalysisContext(
                graph=graph,
                config=self._config,
                investigation_id=str(inv_id),
                execution_id=str(exec_id) if exec_id else None,
            )
            engine = IntelligenceEngine(
                analysis_context,
                auto_register=_ANALYZER_CLASSES,
            )
            results = engine.run()
            t5 = datetime.now(UTC)
            analyzer_duration = (t5 - t4).total_seconds()

            logger.info(
                "analysis_completed",
                investigation_id=inv_str,
                duration_seconds=round(analyzer_duration, 3),
                analyzer_count=len(results.results),
            )

            # ── 5. Aggregate ──────────────────────────────────────
            t6 = datetime.now(UTC)
            landscape = self._aggregator.aggregate(results)
            t7 = datetime.now(UTC)
            aggregation_duration = (t7 - t6).total_seconds()

            # ── 6. Render ─────────────────────────────────────────
            t8 = datetime.now(UTC)
            landscape_resp = landscape_to_response(landscape)
            markdown = self._md_renderer.render(landscape)
            json_data = self._json_renderer.render(landscape)
            t9 = datetime.now(UTC)
            presentation_duration = (t9 - t8).total_seconds()

            logger.info(
                "presentation_completed",
                investigation_id=inv_str,
                duration_seconds=round(presentation_duration, 3),
                markdown_length=len(markdown),
            )

            # ── 7. Persist artifacts ──────────────────────────────
            generated_at = datetime.now(UTC).isoformat()
            artifact_payload_md = {
                "format": "markdown",
                "content": markdown,
                "investigation_id": inv_str,
                "generated_at": generated_at,
            }
            artifact_payload_json = {
                "format": "json",
                "content": json_data,
                "investigation_id": inv_str,
                "generated_at": generated_at,
            }

            self._artifact_service.create_artifact(
                investigation_id=inv_id,
                request=CreateArtifactRequest(
                    artifact_type=ArtifactType.RESEARCH_LANDSCAPE,
                    execution_id=exec_id,
                    payload=artifact_payload_md,
                ),
                status=ArtifactStatus.READY,
            )
            self._artifact_service.create_artifact(
                investigation_id=inv_id,
                request=CreateArtifactRequest(
                    artifact_type=ArtifactType.RESEARCH_LANDSCAPE,
                    execution_id=exec_id,
                    payload=artifact_payload_json,
                ),
                status=ArtifactStatus.READY,
            )

            logger.info(
                "artifacts_created",
                investigation_id=inv_str,
                artifact_type=ArtifactType.RESEARCH_LANDSCAPE.value,
                count=2,
            )

            # ── 8. Store results in context ───────────────────────
            context.add_artifact("intelligence_landscape", landscape_resp)
            context.add_artifact("intelligence_markdown", markdown)
            context.add_artifact("intelligence_json", json_data)

            # ── 9. Record metrics ─────────────────────────────────
            total_duration = (datetime.now(UTC) - stage_start).total_seconds()
            context.record_metric("graph_build_duration", round(graph_duration, 3))
            context.record_metric("analyzer_duration", round(analyzer_duration, 3))
            context.record_metric("aggregation_duration", round(aggregation_duration, 3))
            context.record_metric("presentation_duration", round(presentation_duration, 3))
            context.record_metric("total_intelligence_duration", round(total_duration, 3))
            context.record_metric("intelligence_papers", len(graph.papers))
            context.record_metric("entities_created", entity_count)
            context.record_metric("authors", len(graph.authors))
            context.record_metric("institutions", len(graph.institutions))
            context.record_metric("methodologies", len(graph.methodologies))
            context.record_metric("datasets", len(graph.datasets))
            context.record_metric("technologies", len(graph.technologies))
            context.record_metric("intelligence_load_duration", round(load_duration, 3))

            logger.info(
                "intelligence_completed",
                investigation_id=inv_str,
                duration_seconds=round(total_duration, 3),
                papers=len(graph.papers),
                analyzers=len(results.results),
                observations=len(landscape.observations),
            )

            return PipelineResult.SUCCESS

        except Exception as exc:
            logger.exception(
                "intelligence_stage_failed",
                investigation_id=inv_str,
                error=str(exc),
            )
            context.add_error("intelligence", str(exc), exc)
            context.record_metric(
                "total_intelligence_duration",
                round((datetime.now(UTC) - stage_start).total_seconds(), 3),
            )
            return PipelineResult.FAILED
