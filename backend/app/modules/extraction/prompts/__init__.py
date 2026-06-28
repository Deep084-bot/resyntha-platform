"""Prompt template management for knowledge extraction."""

from app.modules.extraction.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
)
from app.modules.extraction.prompts.template import PromptTemplate

__all__ = [
    "PromptTemplate",
    "EXTRACTION_SYSTEM_PROMPT",
    "build_extraction_user_prompt",
]
