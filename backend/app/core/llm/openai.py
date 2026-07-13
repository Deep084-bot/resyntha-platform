"""OpenAI LLM provider implementation.

Uses the official OpenAI Python SDK.
Prompts the model to return valid JSON matching the required schema.

SDK-specific exceptions (``RateLimitError``, ``APITimeoutError``,
``APIError``) are translated to provider-independent types
(``LLMRateLimitError``, ``LLMTimeoutError``, ``LLMAPIError``)
before leaving the provider.
"""

import asyncio
import json
from collections.abc import AsyncIterator

from openai import (
    APIError as OpenAIAPIError,
)
from openai import (
    APITimeoutError as OpenAITimeoutError,
)
from openai import (
    AsyncOpenAI,
)
from openai import (
    RateLimitError as OpenAIRateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.core.llm.base import BaseLLMProvider, LLMUsage
from app.core.llm.exceptions import (
    LLMAPIError,
    LLMParsingError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.core.llm.parser import parse_llm_json
from app.observability.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """LLM provider powered by OpenAI's API."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        settings = get_settings()
        self._model = model or settings.LLM_MODEL
        self._client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_retries: int = 3,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> tuple[BaseModel, LLMUsage]:
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=180,
                )

                choice = response.choices[0]
                finish_reason = getattr(choice, "finish_reason", None)
                content = choice.message.content or ""

                usage_data = LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    model=self._model,
                )

                parsed = parse_llm_json(
                    raw=content,
                    finish_reason=finish_reason,
                )

                validated = response_model.model_validate(parsed)
                return validated, usage_data

            except LLMParsingError:
                raise

            except (ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning(
                    "llm_validation_failure",
                    attempt=attempt + 1,
                    model=self._model,
                    error=str(exc)[:500],
                )
                if attempt < max_retries - 1:
                    continue
                raise

            except (OpenAIAPIError, OpenAITimeoutError, OpenAIRateLimitError) as exc:
                last_error = exc
                logger.warning(
                    "llm_api_error",
                    attempt=attempt + 1,
                    model=self._model,
                    error=str(exc)[:200],
                )
                if attempt < max_retries - 1:
                    wait = 2**attempt * 2
                    await asyncio.sleep(wait)
                    continue
                if isinstance(exc, OpenAIRateLimitError):
                    raise LLMRateLimitError(
                        f"OpenAI rate limit exceeded after {max_retries} retries",
                    ) from exc
                if isinstance(exc, OpenAITimeoutError):
                    raise LLMTimeoutError(
                        f"OpenAI request timed out after {max_retries} retries",
                    ) from exc
                raise LLMAPIError(
                    f"OpenAI API error after {max_retries} retries: {exc}",
                ) from exc

        msg = f"LLM request failed after {max_retries} retries"
        if isinstance(last_error, (OpenAIAPIError, OpenAITimeoutError, OpenAIRateLimitError)):
            if isinstance(last_error, OpenAIRateLimitError):
                raise LLMRateLimitError(msg) from last_error
            if isinstance(last_error, OpenAITimeoutError):
                raise LLMTimeoutError(msg) from last_error
            raise LLMAPIError(msg) from last_error
        raise RuntimeError(msg) from last_error

    async def generate_stream(  # type: ignore[override]
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=180,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except OpenAIRateLimitError as exc:
            raise LLMRateLimitError(f"OpenAI rate limit during streaming: {exc}") from exc
        except OpenAITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI timeout during streaming: {exc}") from exc
        except OpenAIAPIError as exc:
            raise LLMAPIError(f"OpenAI API error during streaming: {exc}") from exc
