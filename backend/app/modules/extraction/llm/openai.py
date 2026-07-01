"""OpenAI LLM provider implementation.

Uses the OpenAI structured outputs API (``response_format`` with
``json_schema``) when available, falling back to ``json_object``
mode with Pydantic validation.

Retries on transient API errors with exponential back-off.
"""

import json

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.modules.extraction.llm.base import BaseLLMProvider, LLMUsage
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
                    response_format={"type": "json_object"},
                )

                choice = response.choices[0]
                raw = choice.message.content or "{}"
                usage_data = LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    model=self._model,
                )

                parsed = json.loads(raw)
                validated = response_model.model_validate(parsed)
                return validated, usage_data

            except (ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning(
                    "llm_parse_failure",
                    attempt=attempt + 1,
                    model=self._model,
                    error=str(exc)[:200],
                )
                if attempt < max_retries - 1:
                    continue
                raise

            except (APIError, APITimeoutError, RateLimitError) as exc:
                last_error = exc
                logger.warning(
                    "llm_api_error",
                    attempt=attempt + 1,
                    model=self._model,
                    error=str(exc)[:200],
                )
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 2
                    import asyncio
                    await asyncio.sleep(wait)
                    continue
                raise

        msg = f"LLM request failed after {max_retries} retries"
        raise RuntimeError(msg) from last_error
