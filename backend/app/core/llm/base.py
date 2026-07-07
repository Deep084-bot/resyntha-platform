"""Abstract base for LLM providers.

Every provider implements ``generate_structured()`` which accepts
a system prompt, a user prompt, and a Pydantic response model,
and returns a validated instance of that model.

Providers also implement ``generate_stream()`` which yields raw
text tokens for real-time streaming.

Providers translate their SDK-specific exceptions into the
provider-independent exception types defined in ``exceptions.py``
before raising them.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class LLMUsage(BaseModel):
    """Token usage metadata returned by the provider."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


class BaseLLMProvider(ABC):
    """Abstract LLM provider.

    Subclasses wrap a specific API (OpenAI, Anthropic, etc.) and
    handle authentication, request formatting, retries, and response
    parsing.
    """

    @property
    def provider_name(self) -> str:
        """Return the short provider identifier (e.g. ``"groq"``)."""
        return type(self).__name__.lower().replace("provider", "")

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_retries: int = 3,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> tuple[BaseModel, LLMUsage]:
        """Send prompts to the LLM and return a validated response.

        Parameters
        ----------
        system_prompt:
            System-level instructions defining the task.
        user_prompt:
            User message containing the paper content.
        response_model:
            Pydantic model class that the response must conform to.
        max_retries:
            Number of retry attempts on API or parse failure.
        temperature:
            LLM temperature parameter.
        max_tokens:
            Maximum tokens in the response.

        Returns
        -------
        tuple[BaseModel, LLMUsage]
            Validated response model and token usage metadata.

        Raises
        ------
        LLMParsingError
            Response could not be parsed as valid JSON.
        LLMRateLimitError
            Provider rate-limit exceeded after all retries.
        LLMTimeoutError
            Provider request timed out after all retries.
        LLMAPIError
            Provider returned an API error after all retries.
        ValidationError
            Pydantic model validation failed.
        json.JSONDecodeError
            Response was not valid JSON.
        """

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM for a chat completion.

        Parameters are the same as ``generate_structured`` but
        no ``response_model`` is required — the caller receives
        raw text tokens as they are produced.

        Yields
        ------
        str
            A single token (or short text segment) from the LLM.

        Raises
        ------
        LLMRateLimitError
            Provider rate-limit exceeded.
        LLMTimeoutError
            Provider request timed out.
        LLMAPIError
            Provider returned an API error.
        """
