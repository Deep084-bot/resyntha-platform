"""arXiv API provider.

Uses the arXiv OAI-PMH interface which returns Atom XML.  Parses the
XML into canonical ``Paper`` objects and returns a normalised
``RetrievalResult``.
"""

import time
import xml.etree.ElementTree as ET
from datetime import datetime

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

SEARCH_URL = "https://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS_EXT = "http://arxiv.org/schemas/atom"


class ArxivProvider(BaseRetrievalProvider):
    """Search papers via the arXiv API."""

    METADATA = ProviderMetadata(
        name="arxiv",
        display_name="arXiv",
        confidence=0.7,
        supported_domains=["cs", "physics", "math", "stat"],
        coverage="Computer Science, Physics, Mathematics, Statistics",
        requires_api_key=False,
        supports_abstracts=True,
        supports_citations=False,
        supports_doi=True,
        supports_full_text=False,
        priority=30,
    )

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)

    @property
    def metadata(self) -> ProviderMetadata:
        return self.METADATA

    async def health_check(self) -> bool:
        """Check arXiv API reachability with a minimal query."""
        try:
            response = await self._client.get(
                SEARCH_URL,
                params={"search_query": "test", "start": 0, "max_results": 1},
                timeout=10.0,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def search(self, query: str, limit: int = 10) -> RetrievalResult:
        """Search arXiv and return normalised results."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 100),
        }
        logger.info("arxiv_search_started", query=query, limit=limit)

        start = time.monotonic()
        try:
            response = await self._client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            raw = response.text
        except httpx.HTTPStatusError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("arxiv_search_failed", query=query, error=str(exc))
            if exc.response.status_code == 429:
                raise RetrievalRateLimitError(
                    "arXiv rate limit exceeded",
                    response_time_ms=round(elapsed, 2),
                ) from exc
            raise RetrievalAPIError(
                f"arXiv HTTP error {exc.response.status_code}",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.ConnectError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("arxiv_search_connection_failed", query=query, error=str(exc))
            raise RetrievalConnectionError(
                "arXiv connection failed",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.TimeoutException as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("arxiv_search_timeout", query=query, error=str(exc))
            raise RetrievalTimeoutError(
                "arXiv request timed out",
                response_time_ms=round(elapsed, 2),
            ) from exc
        except httpx.HTTPError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("arxiv_search_failed", query=query, error=str(exc))
            raise RetrievalAPIError(
                f"arXiv request failed: {exc}",
                response_time_ms=round(elapsed, 2),
            ) from exc

        elapsed = (time.monotonic() - start) * 1000
        papers = self._parse_feed(raw)
        logger.info("arxiv_search_completed", query=query, count=len(papers))
        return RetrievalResult(
            papers=papers,
            provider_name=self.name,
            response_time_ms=round(elapsed, 2),
            papers_returned=len(papers),
            success=True,
        )

    def _parse_feed(self, raw: str) -> list[Paper]:
        """Parse the Atom XML response into a list of ``Paper`` objects."""
        root = ET.fromstring(raw)
        papers: list[Paper] = []

        for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
            doi = _text(entry, f"{{{ARXIV_NS_EXT}}}doi")
            published_str = _text(entry, f"{{{ARXIV_NS}}}published")
            published: datetime | None = None
            if published_str:
                try:
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published = None

            url = _attr(entry, f"{{{ARXIV_NS}}}link", "href")

            # Extract arXiv ID from the URL
            arxiv_id = None
            if url and "/abs/" in url:
                arxiv_id = url.split("/abs/", 1)[-1]

            authors = []
            for author_el in entry.findall(f"{{{ARXIV_NS}}}author"):
                name = _text(author_el, f"{{{ARXIV_NS}}}name")
                if name:
                    authors.append(name)

            papers.append(
                Paper(
                    title=_text(entry, f"{{{ARXIV_NS}}}title", "").replace("\n", " ").strip(),
                    abstract=_text(entry, f"{{{ARXIV_NS}}}summary", "").replace("\n", " ").strip()
                    or None,
                    authors=authors,
                    year=published.year if published else None,
                    doi=doi,
                    url=url,
                    source=self.name,
                    metadata={
                        "external_ids": {
                            "arxiv": arxiv_id,
                            "doi": doi,
                        },
                    },
                )
            )

        return papers


def _text(element: ET.Element, path: str, default: str | None = None) -> str | None:
    child = element.find(path)
    return child.text if child is not None else default


def _attr(element: ET.Element, path: str, attr: str, default: str | None = None) -> str | None:
    child = element.find(path)
    return child.get(attr) if child is not None else default
