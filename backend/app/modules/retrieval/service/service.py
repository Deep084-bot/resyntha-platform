"""Retrieval service — orchestrates the full paper-fetch pipeline.

Delegates to ``RetrievalCoordinator`` which runs all configured
providers concurrently, merges, deduplicates, and ranks.  Persistence
is handled by the caller (``RetrieveStage`` + ``PersistStage``).

Providers are obtained from ``RetrievalProviderRegistry`` instead of
being instantiated directly.
"""

from collections.abc import Sequence

from app.core.retrieval import BaseRetrievalProvider, RetrievalProviderRegistry
from app.modules.retrieval.coordinator.coordinator import RetrievalCoordinator
from app.modules.retrieval.domain.paper import Paper
from app.observability.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    """Search external providers, normalise, deduplicate, and rank papers.

    Parameters
    ----------
    providers:
        Optional pre-configured provider instances for dependency
        injection / testing.  When ``None``, providers are obtained
        from ``RetrievalProviderRegistry.create_active()``.
    redis:
        Optional Redis client for caching (passed to coordinator).
    cache_ttl:
        Cache TTL in seconds (default 3600).
    """

    def __init__(
        self,
        providers: Sequence[BaseRetrievalProvider] | None = None,
        redis: object | None = None,
        cache_ttl: int = 3600,
    ) -> None:
        if providers is None:
            provider_list = RetrievalProviderRegistry.create_active()
        else:
            provider_list = list(providers)

        self._coordinator = RetrievalCoordinator(
            providers=provider_list,
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
