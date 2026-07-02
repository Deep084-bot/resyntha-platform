"""Semantic Scholar API provider.

Uses the Semantic Scholar Paper Search API (no key required for the
basic endpoint).  Returns normalised ``RetrievalResult`` with canonical
``Paper`` objects.
"""

import time

import httpx

from app.core.retrieval.base import BaseRetrievalProvider, ProviderMetadata, RetrievalResult
from app.core.retrieval.exceptions import (
    RetrievalAPIError,
    RetrievalConnectionError,
    RetrievalRateLimitError,
    RetrievalTimeoutError,
)
from app.core.retrieval.paper import Paper
from app.observability.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,venue,externalIds,url,citationCount"


class SemanticScholarProvider(BaseRetrievalProvider):
    """Search papers via the Semantic Scholar API."""

    METADATA = ProviderMetadata(
        name="semantic_scholar",
        display_name="Semantic Scholar",
        confidence=1.0,
        supported_domains=["cs", "biology", "medicine", "physics"],
        coverage="Computer Science, Biology, Medicine, Physics",
        requires_api_key=False,
        supports_abstracts=True,
        supports_citations=True,
        supports_doi=True,
        supports_full_text=False,
        priority=10,
    )

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)

    @property
    def metadata(self) -> ProviderMetadata:
        return self.METADATA

    async def health_check(self) -> bool:
        """Check Semantic Scholar API reachability with a minimal query."""
        try:
            response = await self._client.get(
                SEARCH_URL,
                params={"query": "test", "limit": 1, "fields": "title"},
                timeout=10.0,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def search(self, query: str, limit: int = 10) -> RetrievalResult:
        """Search Semantic Scholar and return normalised results."""
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": FIELDS,
        }
        logger.info("ss_search_started", query=query, limit=limit)

        start = time.monotonic()
        try:
            response = await self._client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("ss_search_failed", query=query, error=str(exc))
            if exc.response.status_code == 429:
                raise RetrievalRateLimitError(
                    "Semantic Scholar rate limit exceeded",
                    response_time_ms=round(elapsed, 2),
                ) from exc
            raise RetrievalAPIError(
                f"Semantic Scholar HTTP error {exc.response.status_code}",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.ConnectError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("ss_search_connection_failed", query=query, error=str(exc))
            raise RetrievalConnectionError(
                "Semantic Scholar connection failed",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.TimeoutException as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("ss_search_timeout", query=query, error=str(exc))
            raise RetrievalTimeoutError(
                "Semantic Scholar request timed out",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.HTTPError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("ss_search_failed", query=query, error=str(exc))
            raise RetrievalAPIError(
                f"Semantic Scholar request failed: {exc}",
                response_time_ms=round(elapsed, 2),
            ) from exc

        elapsed = (time.monotonic() - start) * 1000
        raw_results = data.get("data", [])
        papers = [self._normalize(raw) for raw in raw_results]
        logger.info("ss_search_completed", query=query, count=len(papers))
        return RetrievalResult(
            papers=papers,
            provider_name=self.name,
            response_time_ms=round(elapsed, 2),
            papers_returned=len(papers),
            success=True,
        )

    def _normalize(self, raw: dict) -> Paper:
        authors = []
        for a in raw.get("authors") or []:
            if isinstance(a, dict) and "name" in a:
                authors.append(a["name"])

        external_ids = raw.get("externalIds") or {}
        doi = external_ids.get("DOI")
        if not doi:
            doi = self._extract_doi_from_url(raw.get("url", ""))

        metadata: dict = {
            "external_ids": {
                "semantic_scholar": external_ids.get("CorpusId"),
                "arxiv": external_ids.get("ArXiv"),
                "doi": external_ids.get("DOI"),
            },
        }

        return Paper(
            title=raw.get("title", "").strip(),
            abstract=raw.get("abstract"),
            authors=authors,
            year=raw.get("year"),
            venue=raw.get("venue"),
            doi=doi,
            url=raw.get("url"),
            citation_count=raw.get("citationCount"),
            source=self.name,
            metadata=metadata,
        )

    @staticmethod
    def _extract_doi_from_url(url: str) -> str | None:
        if not url:
            return None
        if "/doi.org/" in url:
            return url.split("/doi.org/", 1)[-1]
        return None
