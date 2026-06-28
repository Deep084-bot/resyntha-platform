"""Retrieval service — orchestrates the full paper-fetch pipeline.

Delegates to ``RetrievalCoordinator`` which runs all configured
providers concurrently, merges, deduplicates, and ranks.  Persistence
is handled by the caller (``RetrieveStage`` + ``PersistStage``).
"""

from collections.abc import Sequence

from app.modules.retrieval.coordinator.coordinator import RetrievalCoordinator
from app.modules.retrieval.domain.paper import Paper
from app.modules.retrieval.providers.arxiv import ArxivProvider
from app.modules.retrieval.providers.openalex import OpenAlexProvider
from app.modules.retrieval.providers.semantic_scholar import (
    SemanticScholarProvider,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    """Search external providers, normalise, deduplicate, and rank papers."""

    def __init__(
        self,
        semantic_scholar: SemanticScholarProvider | None = None,
        arxiv: ArxivProvider | None = None,
        openalex: OpenAlexProvider | None = None,
        redis: object | None = None,
        cache_ttl: int = 3600,
    ) -> None:
        providers = [
            semantic_scholar or SemanticScholarProvider(),
            arxiv or ArxivProvider(),
            openalex or OpenAlexProvider(email=None),
        ]
        self._coordinator = RetrievalCoordinator(
            providers=providers,
            redis=redis,
            cache_ttl=cache_ttl,
        )

    async def retrieve(
        self,
        query: str,
        paper_limit: int = 10,
    ) -> Sequence[Paper]:
        """Search providers, merge, deduplicate, and rank.

        Returns a score-descending list of canonical ``Paper`` objects
        without persisting them.
        """
        logger.info("retrieval_started", query=query, paper_limit=paper_limit)
        papers, metrics = await self._coordinator.retrieve(query, paper_limit)
        logger.info("retrieval_completed", total=len(papers), metrics=metrics)
        return papers

    async def retrieve_with_metrics(
        self,
        query: str,
        paper_limit: int = 10,
    ) -> tuple[Sequence[Paper], dict]:
        """Like ``retrieve()`` but also returns coordinator metrics.

        Use this when the caller wants to persist metrics to the
        execution's metadata.
        """
        logger.info(
            "retrieval_with_metrics_started",
            query=query,
            paper_limit=paper_limit,
        )
        papers, metrics = await self._coordinator.retrieve(query, paper_limit)
        logger.info(
            "retrieval_with_metrics_completed",
            total=len(papers),
            metrics=metrics,
        )
        return papers, metrics
