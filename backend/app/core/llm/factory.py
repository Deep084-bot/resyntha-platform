"""Provider factory — map a provider name to a provider instance.

Usage::

    from app.core.llm.factory import ProviderFactory

    provider = ProviderFactory.create("groq")
    result, usage = await provider.generate_structured(...)
"""

from app.core.llm.base import BaseLLMProvider
from app.core.llm.groq import GroqProvider

_PROVIDER_REGISTRY: dict[str, type[BaseLLMProvider]] = {}


def register_provider(name: str, provider_cls: type[BaseLLMProvider]) -> None:
    """Register a provider class under a short identifier.

    The identifier should match the value used in configuration
    (e.g. ``"groq"``, ``"openai"``).
    """
    _PROVIDER_REGISTRY[name] = provider_cls


def _discover_providers() -> None:
    """Import and register all known built-in providers.

    Called once lazily on the first ``ProviderFactory.create()`` call.
    """
    if _PROVIDER_REGISTRY:
        return

    from app.core.llm.groq import GroqProvider

    register_provider("groq", GroqProvider)

    try:
        from app.core.llm.openai import OpenAIProvider

        register_provider("openai", OpenAIProvider)
    except ImportError:
        pass


class ProviderFactory:
    """Create and return LLM provider instances."""

    @staticmethod
    def create(provider_name: str | None = None, **kwargs) -> BaseLLMProvider:
        """Return a provider instance for *provider_name*.

        Parameters
        ----------
        provider_name:
            Short provider identifier (``"groq"``, ``"openai"``).
            Falls back to ``"groq"`` when ``None``.

        **kwargs:
            Forwarded to the provider constructor (e.g. ``model``, ``api_key``).

        Raises
        ------
        ValueError
            Unknown provider name.
        """
        _discover_providers()

        name = provider_name or "groq"
        provider_cls = _PROVIDER_REGISTRY.get(name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown LLM provider: {name!r}. "
                f"Available: {list(_PROVIDER_REGISTRY)}",
            )
        return provider_cls(**kwargs)
