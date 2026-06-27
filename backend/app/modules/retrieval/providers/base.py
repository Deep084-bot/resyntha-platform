"""Abstract base provider for paper search.

All external providers (Semantic Scholar, arXiv, …) implement this
interface so the retrieval service can query them interchangeably.
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Interface that every paper-search provider must implement."""

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[dict]:
        """Search for papers matching *query* and return up to *limit* results.

        Returns a list of provider-specific dictionaries.  The
        normaliser is responsible for converting these into the
        canonical ``Paper`` model.
        """
        ...
