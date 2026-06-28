"""Provider factory — instantiates the correct LLM provider by name.

Usage::

    provider = ProviderFactory.create("groq")
    provider = ProviderFactory.create("openai")

No if/else chains across the codebase; selection is driven entirely
by the ``LLM_PROVIDER`` config value.
"""

from app.modules.extraction.llm.base import BaseLLMProvider
from app.modules.extraction.llm.groq import GroqProvider
from app.observability.logger import get_logger

logger = get_logger(__name__)

_providers: dict[str, type[BaseLLMProvider]] = {
    "groq": GroqProvider,
}


def register_provider(name: str, cls: type[BaseLLMProvider]) -> None:
    """Register an additional provider (e.g. OpenAI)."""
    _providers[name.lower()] = cls


# ── Optional providers ──────────────────────────────────────────
try:
    from app.modules.extraction.llm.openai import OpenAIProvider  # noqa: F811
    register_provider("openai", OpenAIProvider)
except ImportError:
    pass


class ProviderFactory:
    """Creates LLM providers by name.

    ``groq`` is available out-of-the-box.  Other providers
    (``openai`` etc.) are registered at import time if their SDKs
    are installed.
    """

    @staticmethod
    def create(provider_name: str, **kwargs: object) -> BaseLLMProvider:
        """Return an instance of the named provider.

        Parameters
        ----------
        provider_name:
            Lowercase provider key (e.g. ``"groq"``, ``"openai"``).
        **kwargs:
            Forwarded to the provider's ``__init__``.

        Raises
        ------
        KeyError
            If the provider name is not registered.
        """
        cls = _providers.get(provider_name.lower())
        if cls is None:
            msg = (
                f"Unknown LLM provider '{provider_name}'. "
                f"Available: {list(_providers)}"
            )
            raise KeyError(msg)
        logger.info(
            "llm_provider_created",
            provider=provider_name,
            provider_class=cls.__name__,
        )
        return cls(**kwargs)
