"""Abstract base provider for paper search.

All external providers (Semantic Scholar, arXiv, …) implement this
interface so the retrieval service can query them interchangeably.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.modules.retrieval.domain.paper import Paper


class SearchResult(BaseModel):
    """Normalised result from a single provider search."""

    papers: list[Paper]
    provider_name: str
    response_time_ms: float = 0.0
    papers_returned: int = 0
    success: bool = True
    error: str | None = None


class BaseProvider(ABC):
    """Interface that every paper-search provider must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier (e.g. 'semantic_scholar')."""
        ...

    @abstractmethod
    async def search(self, query: str, limit: int) -> SearchResult:
        """Search for papers matching *query* and return up to *limit* results.

        Returns a ``SearchResult`` containing normalised ``Paper`` objects
        along with execution metadata.
        """
        ...
