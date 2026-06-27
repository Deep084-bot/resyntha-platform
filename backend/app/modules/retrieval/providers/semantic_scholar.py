"""Semantic Scholar API provider.

Uses the Semantic Scholar Paper Search API (no key required for the
basic endpoint).  Returns raw JSON blobs that the normaliser converts
into the canonical ``Paper`` model.
"""

import httpx

from app.modules.retrieval.providers.base import BaseProvider
from app.observability.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,venue,externalIds,url,citationCount"


class SemanticScholarProvider(BaseProvider):
    """Search papers via the Semantic Scholar API."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search Semantic Scholar and return raw result dicts."""
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": FIELDS,
        }
        logger.info("ss_search_started", query=query, limit=limit)

        try:
            response = await self._client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error("ss_search_failed", query=query, error=str(exc))
            return []

        results = data.get("data", [])
        logger.info("ss_search_completed", query=query, count=len(results))
        return results
