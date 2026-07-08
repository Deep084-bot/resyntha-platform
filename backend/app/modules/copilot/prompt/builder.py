"""Prompt builder — constructs system and user prompts for the Copilot."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.copilot.retrieval.models import RetrievalResult


class LLMCopilotAnswer(BaseModel):
    """Structured response from the LLM for a single chat turn."""

    answer: str = Field(..., description="The assistant's answer to the user's question.")
    citations: list[dict] = Field(
        default_factory=list,
        description="List of citation objects with paper_title and relevance keys.",
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score 0.0–1.0 for the answer based on available evidence.",
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of how the answer was derived from the context.",
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="3–5 contextual follow-up questions a researcher might ask next.",
    )


SYSTEM_PROMPT_TEMPLATE = """You are a research assistant analysing academic papers and investigation data.

## Rules
1. Answer ONLY from the provided investigation context. Never use external knowledge or invent papers, authors, metrics, or findings.
2. Cite papers using exact titles from the context. Distinguish direct evidence from inference.
3. If the context lacks information, state: "I cannot answer this from the current investigation."
4. Suggest 3–5 follow-up questions grounded in methodologies, technologies, datasets, gaps, or limitations in the context.
5. Return ONLY valid JSON with no markdown fences or extra text. Use this format:

{{
  "answer": "...",
  "citations": [{{"paper_title": "...", "relevance": "..."}}],
  "confidence": 0.0–1.0,
  "reasoning": "...",
  "suggested_questions": ["...", "..."]
}}

## Context

{context}
{history_section}
## Question

{question}"""


class PromptBuilder:
    """Constructs system and user prompts for the investigation-aware Copilot.

    Receives a ``RetrievalResult`` with scored sections instead of raw context.
    The prompt clearly separates Context, Conversation, and Question sections.
    """

    def __init__(self) -> None:
        self._system_sections: list[str] = []

    def build_system_prompt(
        self,
        retrieved: RetrievalResult,
        history: str = "",
    ) -> str:
        context_text = self._format_sections(retrieved)

        history_section = ""
        if history:
            history_section = f"\n## Previous Conversation\n\n{history}\n"

        return SYSTEM_PROMPT_TEMPLATE.format(
            context=context_text,
            history_section=history_section,
            question="{question}",
        ).replace('{question}', '{question}')  # literal placeholder for user prompt

    def build_user_prompt(self, history: str, question: str) -> str:
        if history:
            return (
                f"Previous conversation:\n{history}\n\n"
                f"Question: {question}"
            )
        return f"Question: {question}"

    def get_response_model(self) -> type[BaseModel]:
        return LLMCopilotAnswer

    @staticmethod
    def _format_sections(retrieved: RetrievalResult) -> str:
        if not retrieved.sections:
            return "No relevant investigation sections found."

        parts: list[str] = []
        for section in retrieved.sections:
            parts.append(
                f"[{section.source} / {section.label}]\n{section.content}"
            )
        return "\n\n".join(parts)
