"""arXiv API provider.

Uses the arXiv OAI-PMH interface which returns Atom XML.  Parses the
XML into plain dicts that the normaliser converts into the canonical
``Paper`` model.
"""

import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from app.modules.retrieval.providers.base import BaseProvider
from app.observability.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "http://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS_EXT = "http://arxiv.org/schemas/atom"


class ArxivProvider(BaseProvider):
    """Search papers via the arXiv API."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search arXiv and return raw result dicts."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 100),
        }
        logger.info("arxiv_search_started", query=query, limit=limit)

        try:
            response = await self._client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            raw = response.text
        except httpx.HTTPError as exc:
            logger.error("arxiv_search_failed", query=query, error=str(exc))
            return []

        results = self._parse_feed(raw)
        logger.info("arxiv_search_completed", query=query, count=len(results))
        return results

    @staticmethod
    def _parse_feed(raw: str) -> list[dict]:
        """Parse the Atom XML response into a list of dicts."""
        root = ET.fromstring(raw)
        entries = []

        for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
            paper: dict = {}

            paper["id"] = _text(entry, f"{{{ARXIV_NS}}}id")
            paper["title"] = _text(entry, f"{{{ARXIV_NS}}}title", "").replace(
                "\n", " "
            ).strip()
            paper["summary"] = _text(
                entry, f"{{{ARXIV_NS}}}summary", ""
            ).replace("\n", " ").strip()
            paper["link"] = _attr(entry, f"{{{ARXIV_NS}}}link", "href")
            paper["doi"] = _text(entry, f"{{{ARXIV_NS_EXT}}}doi")

            published = _text(entry, f"{{{ARXIV_NS}}}published")
            if published:
                try:
                    paper["published"] = datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    paper["published"] = None
            else:
                paper["published"] = None

            authors = []
            for author_el in entry.findall(f"{{{ARXIV_NS}}}author"):
                name = _text(author_el, f"{{{ARXIV_NS}}}name")
                if name:
                    authors.append(name)
            paper["authors"] = authors

            entries.append(paper)

        return entries


def _text(element: ET.Element, path: str, default: str | None = None) -> str | None:
    child = element.find(path)
    return child.text if child is not None else default


def _attr(
    element: ET.Element, path: str, attr: str, default: str | None = None
) -> str | None:
    child = element.find(path)
    return child.get(attr) if child is not None else default
