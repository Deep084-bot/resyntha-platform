"""RetrievalCoordinator — orchestrates providers, merges, deduplicates, ranks.

Runs all registered providers concurrently via ``asyncio.gather``,
collects latency and error metrics per provider, merges duplicates
across providers, resolves remaining duplicates within the merged
set, ranks deterministically, and returns the final paper list with
execution metadata.
"""

import asyncio
import json
from collections.abc import Sequence

from app.core.retrieval.base import BaseRetrievalProvider, RetrievalResult
from app.modules.retrieval.coordinator.merger import MetadataMerger
from app.modules.retrieval.coordinator.ranking import RankingEngine
from app.modules.retrieval.coordinator.resolver import DuplicateResolver
from app.modules.retrieval.domain.paper import Paper
from app.observability.logger import get_logger

logger = get_logger(__name__)


def _decode_retrieval_result(data: dict) -> RetrievalResult:
    """Decode a JSON dict back into a RetrievalResult (Pydantic v2)."""
    papers = [Paper.model_validate(p) for p in data.get("papers", [])]
    return RetrievalResult(
        papers=papers,
        papers_returned=data["papers_returned"],
        response_time_ms=data["response_time_ms"],
        error=data.get("error"),
        success=data.get("success", True),
    )


class CachedProvider:
    """Optional caching wrapper around a ``BaseRetrievalProvider``.

    Uses JSON over Redis for serialization (avoids pickle security and
    performance overhead).  Skips cache entirely when ``redis`` is
    ``None``.
    """

    def __init__(
        self,
        provider: BaseRetrievalProvider,
        redis: object | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._provider = provider
        self._redis = redis
        self._ttl = ttl_seconds

    @property
    def name(self) -> str:
        return self._provider.name

    async def search(self, query: str, limit: int) -> RetrievalResult:
        if self._redis is None:
            return await self._provider.search(query, limit)

        key = f"provider:{self._provider.name}:{query}:{limit}"
        try:
            cached = await self._get_cached(key)
            if cached is not None:
                logger.info(
                    "cache_hit",
                    provider=self._provider.name,
                    query=query,
                )
                return cached
        except Exception:
            logger.warning("cache_read_failed", provider=self._provider.name)

        result = await self._provider.search(query, limit)
        try:
            await self._set_cached(key, result)
        except Exception:
            logger.warning("cache_write_failed", provider=self._provider.name)
        return result

    async def _get_cached(self, key: str) -> RetrievalResult | None:
        data = await self._redis.get(key)
        if data is None:
            return None
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return _decode_retrieval_result(json.loads(data))

    async def _set_cached(self, key: str, result: RetrievalResult) -> None:
        raw = json.dumps(result.model_dump(mode="json"))
        await self._redis.setex(key, self._ttl, raw)


class RetrievalCoordinator:
    """Orchestrates multiple providers with merging, dedup, ranking, and caching."""

    def __init__(
        self,
        providers: Sequence[BaseRetrievalProvider],
        resolver: DuplicateResolver | None = None,
        merger: MetadataMerger | None = None,
        ranking: RankingEngine | None = None,
        redis: object | None = None,
        cache_ttl: int = 3600,
    ) -> None:
        self._providers = providers
        self._resolver = resolver or DuplicateResolver()
        self._merger = merger or MetadataMerger()
        self._ranking = ranking or RankingEngine()
        self._redis = redis
        self._cache_ttl = cache_ttl

    async def retrieve(self, query: str, limit: int = 10) -> tuple[list[Paper], dict]:
        """Run all providers, collect metrics, and return ranked papers.

        Returns ``(papers, metrics)`` where ``metrics`` contains:
        - ``providers``: per-provider stats
        - ``papers_fetched``: total papers before dedup
        - ``papers_unique``: papers after dedup
        - ``papers_final``: final ranked count
        - ``duplicates_removed``: count of duplicates
        - ``average_score``: mean score across final papers
        - ``cache_enabled``: whether caching was active
        """
        providers_with_cache = [
            CachedProvider(p, redis=self._redis, ttl_seconds=self._cache_ttl)
            for p in self._providers
        ]

        tasks = [p.search(query, limit) for p in providers_with_cache]
        logger.info("coordinator_search_started", provider_count=len(self._providers), query=query)
        results: list[RetrievalResult | Exception] = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers: list[Paper] = []
        provider_metrics: dict[str, dict] = {}

        for provider, result in zip(self._providers, results):
            name = provider.name
            if isinstance(result, Exception):
                rt_ms = getattr(result, "response_time_ms", 0)
                logger.error("provider_failed", provider=name, error=str(result))
                provider_metrics[name] = {
                    "success": False,
                    "error": str(result),
                    "papers_returned": 0,
                    "response_time_ms": rt_ms,
                }
                continue

            all_papers.extend(result.papers)
            provider_metrics[name] = {
                "success": result.success,
                "error": result.error,
                "papers_returned": result.papers_returned,
                "response_time_ms": result.response_time_ms,
            }
            logger.info("provider_succeeded", provider=name, papers_returned=result.papers_returned, latency_ms=result.response_time_ms)

        papers_fetched = len(all_papers)
        logger.info("coordinator_merge_started", total_papers=papers_fetched)

        merged = self._merger.merge(all_papers)
        deduped = self._resolver.resolve(merged)
        ranked = self._ranking.rank(deduped)

        duplicates_removed = papers_fetched - len(ranked)
        avg_score = (
            round(sum(p.score for p in ranked) / len(ranked), 2) if ranked else 0.0
        )

        metrics: dict = {
            "providers": provider_metrics,
            "papers_fetched": papers_fetched,
            "papers_unique": len(ranked),
            "duplicates_removed": duplicates_removed,
            "average_score": avg_score,
            "cache_enabled": self._redis is not None,
        }
        logger.info(
            "coordinator_completed",
            papers_fetched=papers_fetched,
            papers_unique=len(ranked),
            duplicates_removed=duplicates_removed,
            average_score=avg_score,
            cache_enabled=self._redis is not None,
        )
        return ranked, metrics
