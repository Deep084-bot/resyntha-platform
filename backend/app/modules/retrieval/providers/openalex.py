"""OpenAlex API provider.

Uses the public OpenAlex API (no key required at low rate limits).
Returns normalised ``SearchResult`` with canonical ``Paper`` objects.
"""

import time

import httpx

from app.modules.retrieval.domain.paper import Paper
from app.modules.retrieval.providers.base import BaseProvider, SearchResult
from app.observability.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.openalex.org/works"


class OpenAlexProvider(BaseProvider):
    """Search papers via the OpenAlex API."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        email: str | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._email = email

    @property
    def name(self) -> str:
        return "openalex"

    async def search(self, query: str, limit: int = 10) -> SearchResult:
        """Search OpenAlex and return normalised results."""
        params = {
            "search": query,
            "per_page": min(limit, 200),
        }
        headers = {}
        if self._email:
            headers["User-Agent"] = f"mailto:{self._email}"

        logger.info("openalex_search_started", query=query, limit=limit)

        start = time.monotonic()
        try:
            response = await self._client.get(
                SEARCH_URL, params=params, headers=headers or None,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("openalex_search_failed", query=query, error=str(exc))
            return SearchResult(
                papers=[],
                provider_name=self.name,
                response_time_ms=round(elapsed, 2),
                papers_returned=0,
                success=False,
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        raw_results = data.get("results", [])
        papers = [self._normalize(raw) for raw in raw_results]
        logger.info("openalex_search_completed", query=query, count=len(papers))
        return SearchResult(
            papers=papers,
            provider_name=self.name,
            response_time_ms=round(elapsed, 2),
            papers_returned=len(papers),
            success=True,
        )

    def _normalize(self, raw: dict) -> Paper:
        doi = raw.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.split("https://doi.org/", 1)[-1]

        authors = []
        for authorship in raw.get("authorships") or []:
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        openalex_id = raw.get("id", "")
        if openalex_id:
            openalex_id = openalex_id.replace("https://openalex.org/", "")

        metadata: dict = {
            "external_ids": {
                "openalex": openalex_id,
                "doi": doi,
            },
        }

        return Paper(
            title=raw.get("title", "").strip(),
            abstract=raw.get("abstract_inverted_index") and self._reconstruct_abstract(
                raw["abstract_inverted_index"]
            ) or None,
            authors=authors,
            year=raw.get("publication_year"),
            venue=self._extract_venue(raw),
            doi=doi,
            url=raw.get("doi") or raw.get("id"),
            citation_count=raw.get("cited_by_count"),
            source=self.name,
            metadata=metadata,
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict) -> str:
        """Reconstruct abstract text from OpenAlex's inverted index format.

        The inverted index maps words to lists of positions:
        ``{"word": [pos1, pos2], ...}``
        """
        if not inverted_index:
            return ""
        word_positions: dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions[pos] = word
        if not word_positions:
            return ""
        max_pos = max(word_positions.keys())
        return " ".join(
            word_positions.get(i, "")
            for i in range(max_pos + 1)
        ).strip()

    @staticmethod
    def _extract_venue(raw: dict) -> str | None:
        primary_location = raw.get("primary_location") or {}
        source = primary_location.get("source") or {}
        display_name = source.get("display_name")
        if display_name:
            return display_name
        # Fallback: check host_organization
        host = primary_location.get("source") or {}
        return host.get("display_name")
