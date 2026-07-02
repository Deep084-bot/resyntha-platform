"""Abstract base for retrieval providers.

Every provider implements ``search()`` and ``health_check()`` and
exposes rich ``metadata`` so the coordinator and registry can make
intelligent decisions without knowing provider internals.

Providers translate their SDK/HTTP exceptions into the
provider-independent exception types defined in ``exceptions.py``
before raising them.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.core.retrieval.paper import Paper


class ProviderMetadata(BaseModel):
    """Rich metadata describing a retrieval provider's capabilities.

    This metadata powers intelligent provider routing, UI display,
    and configuration validation.
    """

    name: str
    """Programmatic identifier (e.g. ``"semantic_scholar"``)."""

    display_name: str
    """Human-readable label (e.g. ``"Semantic Scholar"``)."""

    confidence: float = 0.5
    """Provider reliability score in ``[0.0, 1.0]``.

    Used by the ranking engine to weight results from this provider.
    """

    supported_domains: list[str] = []
    """Research domains this provider covers well.

    Examples: ``["cs", "physics", "medicine", "biology"]``.
    """

    coverage: str = ""
    """Human description of coverage scope.

    Example: ``"Computer Science, Physics, Mathematics"``.
    """

    requires_api_key: bool = False
    """Whether this provider requires an API key for access."""

    supports_abstracts: bool = True
    """Provider returns abstract text in search results."""

    supports_citations: bool = False
    """Provider returns citation counts."""

    supports_doi: bool = True
    """Provider returns DOIs in search results."""

    supports_full_text: bool = False
    """Provider can return full-text content."""

    priority: int = 0
    """Relative priority when multiple providers are active.

    Higher values are preferred when routing queries.
    """


class RetrievalResult(BaseModel):
    """Normalised result from a single provider search."""

    papers: list[Paper]
    provider_name: str
    response_time_ms: float = 0.0
    papers_returned: int = 0
    success: bool = True
    error: str | None = None


class BaseRetrievalProvider(ABC):
    """Interface that every paper-search provider must implement."""

    @property
    def name(self) -> str:
        """Short provider identifier (e.g. ``\"semantic_scholar\"``).

        Derived from ``metadata.name`` for backward compatibility.
        """
        return self.metadata.name

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return the provider's rich metadata.

        The returned object is typically a class-level constant
        shared across all instances.
        """
        ...

    @abstractmethod
    async def search(self, query: str, limit: int) -> RetrievalResult:
        """Search for papers matching *query* and return up to *limit* results.

        Parameters
        ----------
        query:
            Free-text search query string.
        limit:
            Maximum number of results to return.

        Returns
        -------
        RetrievalResult
            Normalised result with papers and execution metadata.

        Raises
        ------
        RetrievalConnectionError
            Connection could not be established.
        RetrievalRateLimitError
            Provider rate-limited the request.
        RetrievalTimeoutError
            Request timed out.
        RetrievalAPIError
            Provider returned a non-retriable error.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the provider is reachable and operational.

        Implementations should perform a lightweight probe (e.g. a
        single-record lookup) and return ``True`` on success.
        """
        ...
