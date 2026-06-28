"""LLM provider abstraction for knowledge extraction.

Providers
---------
- ``BaseLLMProvider`` — abstract base class every provider implements.
- ``GroqProvider`` — default provider using the Groq SDK.
- ``OpenAIProvider`` — optional provider (requires ``openai`` SDK).

Selection
---------
Use ``ProviderFactory.create("groq")`` to get the default provider.
Provider choice is driven by the ``LLM_PROVIDER`` config value.
"""

from app.modules.extraction.llm.base import BaseLLMProvider
from app.modules.extraction.llm.factory import ProviderFactory, register_provider
from app.modules.extraction.llm.groq import GroqProvider

__all__ = [
    "BaseLLMProvider",
    "GroqProvider",
    "ProviderFactory",
    "register_provider",
]
