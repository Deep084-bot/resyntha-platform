"""Analysis service — cross-paper research landscape computation.

``AnalysisService`` is stateless per run. It:

1. Fetches all ``ExtractedKnowledge`` records for an investigation.
2. Computes frequencies, distributions, rankings, and clusters.
3. Creates a ``RESEARCH_LANDSCAPE`` artifact.

No LLM calls — everything is deterministic aggregation.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.analysis.artifact.builder import AnalysisArtifactBuilder
from app.modules.analysis.cluster.clustering import Clusterer
from app.modules.analysis.domain.landscape import (
    CitationStats,
    PublicationYearDistribution,
    ResearchLandscape,
    VenueDistribution,
)
from app.modules.analysis.statistics.calculator import StatisticsCalculator
from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.paper.domain.models import Paper
from app.observability.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    """Orchestrate cross-paper analysis for an investigation.

    Parameters
    ----------
    session:
        Async SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._extraction_repo = ExtractionRepository(session)
        self._artifact_builder = AnalysisArtifactBuilder(session)
        self._clusterer = Clusterer()
        self._calculator = StatisticsCalculator()

    def analyze(
        self,
        investigation_id: uuid.UUID,
        execution_id: uuid.UUID | None = None,
    ) -> ResearchLandscape:
        """Run cross-paper analysis and create a landscape artifact.

        Returns the computed ``ResearchLandscape``.
        """
        records = self._extraction_repo.list_by_investigation(
            investigation_id,
        )

        landscape = self._compute_landscape(records)

        self._artifact_builder.create_landscape_artifact(
            investigation_id=investigation_id,
            landscape=landscape,
            execution_id=execution_id,
        )

        self._session.commit()

        logger.info(
            "analysis_complete",
            investigation_id=str(investigation_id),
            paper_count=landscape.paper_count,
        )

        return landscape

    def _compute_landscape(
        self,
        records: Sequence[ExtractedKnowledge],
    ) -> ResearchLandscape:
        """Deterministically compute the research landscape from records."""
        paper_count = len(records)

        all_methodologies = self._flatten_field(records, "methodology")
        all_techniques = self._flatten_field(records, "relevant_techniques")
        all_limitations = self._flatten_field(records, "limitations")
        all_future_work = self._flatten_field(records, "future_work")
        all_contributions = self._flatten_field(records, "key_contributions")

        methodologies = self._clusterer.cluster_and_rank(
            all_methodologies,
            min_count=1,
        )
        techniques_ranked = self._clusterer.cluster_and_rank(all_techniques)
        limitations_ranked = self._clusterer.cluster_and_rank(all_limitations)
        future_work_ranked = self._clusterer.cluster_and_rank(all_future_work)
        contributions_ranked = self._clusterer.cluster_and_rank(
            all_contributions,
            min_count=1,
        )

        # ── New data fields ───────────────────────────────────────
        all_datasets = self._flatten_field(records, "datasets_used")
        all_technologies = self._flatten_field(records, "technologies")
        all_metrics = self._flatten_field(records, "evaluation_metrics")
        all_domains = self._flatten_field(records, "research_domains")
        all_authors = self._flatten_field(records, "authors")
        all_keywords = self._flatten_field(records, "keywords")

        datasets_ranked = self._clusterer.cluster_and_rank(all_datasets)
        technologies_ranked = self._clusterer.cluster_and_rank(all_technologies)
        metrics_ranked = self._clusterer.cluster_and_rank(all_metrics)
        domains_ranked = self._clusterer.cluster_and_rank(all_domains)
        authors_ranked = self._clusterer.cluster_and_rank(all_authors)
        keywords_ranked = self._clusterer.cluster_and_rank(all_keywords)

        all_terms = list(
            self._calculator.flatten_list_of_lists(
                [
                    all_techniques,
                    all_limitations,
                    all_future_work,
                    all_contributions,
                    all_datasets,
                    all_technologies,
                    all_metrics,
                    all_domains,
                    all_keywords,
                ],
            ),
        )

        # Use dedicated keywords if available, fall back to term clustering
        keywords = keywords_ranked or self._clusterer.cluster_and_rank(
            all_terms,
            min_count=1,
            max_results=30,
        )

        clusters = self._clusterer.co_occurrence_clusters(all_terms)

        venue_dist = VenueDistribution(
            venues=self._calculator.frequency_distribution(
                self._flatten_field(records, "venue"),
                normalize=False,
            ),
        )

        paper_ids = [r.paper_id for r in records]
        papers = (
            (self._session.query(Paper).filter(Paper.id.in_(paper_ids)).all()) if paper_ids else []
        )

        years = [str(p.year) for p in papers if p.year is not None]
        year_dist = PublicationYearDistribution(
            years=self._calculator.frequency_distribution(years, normalize=False),
        )

        citation_counts = [p.citation_count for p in papers if p.citation_count is not None]
        total_citations = sum(citation_counts)
        citation_stats = CitationStats(
            total_citations=total_citations,
            average_citations=total_citations / max(len(citation_counts), 1),
        )

        return ResearchLandscape(
            paper_count=paper_count,
            methodologies=methodologies,
            datasets=datasets_ranked or techniques_ranked,
            evaluation_metrics=metrics_ranked,
            research_domains=domains_ranked or contributions_ranked,
            tasks=methodologies,
            applications=technologies_ranked or techniques_ranked,
            limitations=limitations_ranked,
            future_work=future_work_ranked,
            keywords=keywords,
            novel_contributions=contributions_ranked,
            top_authors=authors_ranked,
            publication_year_distribution=year_dist,
            venue_distribution=venue_dist,
            citation_statistics=citation_stats,
            clusters=clusters,
            generated_at=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _flatten_field(
        records: Sequence[ExtractedKnowledge],
        field: str,
    ) -> list[str]:
        """Extract and flatten a field from all records.

        If *field* is a list-type column, all items are concatenated.
        If it is a scalar, non-None values are collected as single items.

        For list-of-dict fields (e.g. authors, institutions), the
        ``name`` key is extracted from each dict.  For plain string
        lists, items are used directly.
        """
        result: list[str] = []
        for rec in records:
            value = getattr(rec, field, None)
            if value is None:
                continue
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict):
                        name = v.get("name") or v.get("metric_name") or v.get("dataset_name") or ""
                        if name:
                            result.append(str(name))
                    elif v:
                        result.append(str(v))
            else:
                result.append(str(value))
        return result
