"""Provider registry — map a provider name to a provider instance.

Usage::

    from app.core.retrieval.factory import RetrievalProviderRegistry

    # Single provider
    provider = RetrievalProviderRegistry.create("semantic_scholar")
    result = await provider.search("machine learning", limit=10)

    # All active providers (reads RETRIEVAL_PROVIDERS from Settings)
    providers = RetrievalProviderRegistry.create_active()
    results = await asyncio.gather(
        *(p.search(query, limit) for p in providers),
    )
"""

from collections.abc import Sequence

from app.core.retrieval.base import BaseRetrievalProvider, ProviderMetadata

_PROVIDER_REGISTRY: dict[str, type[BaseRetrievalProvider]] = {}
_DISCOVERED: bool = False


def _discover_providers() -> None:
    """Import and register all known built-in providers.

    Called once lazily on the first registry access.
    """
    global _DISCOVERED
    if _DISCOVERED:
        return

    from app.core.retrieval.arxiv import ArxivProvider
    from app.core.retrieval.openalex import OpenAlexProvider
    from app.core.retrieval.semantic_scholar import SemanticScholarProvider

    register_provider("arxiv", ArxivProvider)
    register_provider("openalex", OpenAlexProvider)
    register_provider("semantic_scholar", SemanticScholarProvider)

    _DISCOVERED = True


def register_provider(name: str, provider_cls: type[BaseRetrievalProvider]) -> None:
    """Register a provider class under a short identifier.

    The identifier should match the value used in configuration
    (e.g. ``"semantic_scholar"``, ``"arxiv"``, ``"openalex"``).
    """
    _PROVIDER_REGISTRY[name] = provider_cls


def list_providers() -> list[str]:
    """Return the names of all registered providers."""
    _discover_providers()
    return list(_PROVIDER_REGISTRY)


def list_provider_metadata() -> list[ProviderMetadata]:
    """Return metadata for all registered providers.

    Instantiates each provider once to read its static metadata.
    Providers are expected to be stateless with respect to metadata.
    """
    _discover_providers()
    result: list[ProviderMetadata] = []
    for name, cls in _PROVIDER_REGISTRY.items():
        try:
            inst = cls()
            result.append(inst.metadata)
        except Exception:
            pass
    return result


class RetrievalProviderRegistry:
    """Create and return retrieval provider instances."""

    @staticmethod
    def create(provider_name: str, **kwargs) -> BaseRetrievalProvider:
        """Return a provider instance for *provider_name*.

        Parameters
        ----------
        provider_name:
            Short provider identifier (``"semantic_scholar"``, ``"arxiv"``,
            ``"openalex"``).

        **kwargs:
            Forwarded to the provider constructor.

        Returns
        -------
        BaseRetrievalProvider
            An instance of the requested provider.

        Raises
        ------
        ValueError
            Unknown provider name.
        """
        _discover_providers()
        provider_cls = _PROVIDER_REGISTRY.get(provider_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown retrieval provider: {provider_name!r}. Available: {list_providers()}",
            )
        return provider_cls(**kwargs)

    @staticmethod
    def create_active(
        provider_names: Sequence[str] | None = None,
    ) -> list[BaseRetrievalProvider]:
        """Create instances of all active providers.

        When *provider_names* is ``None``, reads
        ``RETRIEVAL_PROVIDERS`` from ``Settings`` via
        ``parse_retrieval_providers()``.  Falls back to all registered
        providers if the setting is not available.

        Parameters
        ----------
        provider_names:
            Optional explicit list of provider names to activate.
            When ``None``, uses configuration.

        Returns
        -------
        list[BaseRetrievalProvider]
            Instances of the active providers.
        """
        _discover_providers()
        if provider_names is None:
            try:
                from app.config.settings import parse_retrieval_providers

                provider_names = parse_retrieval_providers()
            except Exception:
                provider_names = list(_PROVIDER_REGISTRY)
        return [RetrievalProviderRegistry.create(name) for name in provider_names]
