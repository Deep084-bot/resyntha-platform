"""Semantic Scholar API provider.

Uses the Semantic Scholar Paper Search API (no key required for the
basic endpoint).  Returns normalised ``SearchResult`` with canonical
``Paper`` objects.
"""

import time

import httpx

from app.modules.retrieval.domain.paper import Paper
from app.modules.retrieval.providers.base import BaseProvider, SearchResult
from app.observability.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,venue,externalIds,url,citationCount"


class SemanticScholarProvider(BaseProvider):
    """Search papers via the Semantic Scholar API."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)

    @property
    def name(self) -> str:
        return "semantic_scholar"

    async def search(self, query: str, limit: int = 10) -> SearchResult:
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
        except httpx.HTTPError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("ss_search_failed", query=query, error=str(exc))
            return SearchResult(
                papers=[],
                provider_name=self.name,
                response_time_ms=round(elapsed, 2),
                papers_returned=0,
                success=False,
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        raw_results = data.get("data", [])
        papers = [self._normalize(raw) for raw in raw_results]
        logger.info("ss_search_completed", query=query, count=len(papers))
        return SearchResult(
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
