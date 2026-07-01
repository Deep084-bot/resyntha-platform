"""Groq LLM provider implementation.

Uses the official Groq Python SDK (OpenAI-compatible endpoint).
Prompts the model to return valid JSON matching the required schema
— standard ``json_object`` mode is not available on all Groq models,
so we rely on prompt instructions plus ``parse_llm_json()``.

Retries on transient API errors with exponential back-off.
"""

import asyncio
import json

from groq import APIError, APITimeoutError, AsyncGroq, RateLimitError
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.modules.extraction.llm.base import BaseLLMProvider, LLMUsage
from app.modules.extraction.llm.exceptions import LLMParsingError
from app.modules.extraction.llm.parser import parse_llm_json
from app.observability.logger import get_logger

logger = get_logger(__name__)


class GroqProvider(BaseLLMProvider):
    """LLM provider powered by Groq's API (OpenAI-compatible)."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        settings = get_settings()
        self._model = model or settings.LLM_MODEL
        self._client = AsyncGroq(api_key=api_key or settings.GROQ_API_KEY)

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

            except LLMParsingError as exc:
                last_error = exc
                logger.warning(
                    "llm_parse_failure",
                    attempt=attempt + 1,
                    model=self._model,
                    raw_repr=repr(exc.raw)[:500],
                    sanitized_repr=repr(exc.sanitized)[:500],
                    finish_reason=exc.finish_reason,
                )
                if attempt < max_retries - 1:
                    continue
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

            except (APIError, APITimeoutError, RateLimitError) as exc:
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
                raise

        msg = f"LLM request failed after {max_retries} retries"
        raise RuntimeError(msg) from last_error
