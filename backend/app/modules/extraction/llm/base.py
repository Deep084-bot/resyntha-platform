"""Abstract base for LLM providers.

Every provider implements ``generate_structured()`` which accepts
a system prompt, a user prompt, and a Pydantic response model,
and returns a validated instance of that model.
"""

from abc import ABC, abstractmethod

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
        """
