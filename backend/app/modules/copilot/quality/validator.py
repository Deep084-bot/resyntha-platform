"""Citation validation — verifies LLM citations against retrieved context."""

from __future__ import annotations

import re

from app.modules.copilot.retrieval.models import RetrievalResult
from app.modules.copilot.schemas.response import Citation


class CitationValidationResult:
    """Result of validating LLM citations against the retrieved context."""

    def __init__(
        self,
        validated: list[Citation],
        discarded: list[Citation],
        total_examined: int,
        kept_count: int,
        discarded_count: int,
    ) -> None:
        self.validated = validated
        self.discarded = discarded
        self.total_examined = total_examined
        self.kept_count = kept_count
        self.discarded_count = discarded_count

    @property
    def success_ratio(self) -> float:
        if self.total_examined == 0:
            return 1.0
        return self.kept_count / self.total_examined


class CitationValidator:
    """Validates citations returned by the LLM against the retrieved investigation context.

    A citation is considered valid if its paper_title (or a close variant)
    appears in at least one of the retrieved sections.
    """

    def validate(
        self,
        raw_citations: list[dict],
        retrieved: RetrievalResult,
    ) -> CitationValidationResult:
        if not raw_citations:
            return CitationValidationResult(
                validated=[], discarded=[], total_examined=0,
                kept_count=0, discarded_count=0,
            )

        context_text = self._build_context_text(retrieved)
        validated: list[Citation] = []
        discarded: list[Citation] = []

        for raw in raw_citations:
            title = (
                raw.get("paper_title", "")
                if isinstance(raw, dict)
                else ""
            )
            relevance = (
                raw.get("relevance", "")
                if isinstance(raw, dict)
                else ""
            )

            citation = Citation(
                paper_title=title,
                paper_id=raw.get("paper_id", "") if isinstance(raw, dict) else "",
                relevance=relevance,
            )

            if self._citation_exists(title, context_text):
                validated.append(citation)
            else:
                discarded.append(citation)

        return CitationValidationResult(
            validated=validated,
            discarded=discarded,
            total_examined=len(raw_citations),
            kept_count=len(validated),
            discarded_count=len(discarded),
        )

    @staticmethod
    def _build_context_text(retrieved: RetrievalResult) -> str:
        parts: list[str] = []
        for section in retrieved.sections:
            parts.append(f"{section.source} / {section.label}\n{section.content}")
        return "\n\n".join(parts)

    @staticmethod
    def _citation_exists(title: str, context_text: str) -> bool:
        if not title:
            return False
        title_lower = title.strip().lower()
        context_lower = context_text.lower()

        if title_lower in context_lower:
            return True

        # Strip parenthetical suffixes like "(2024)", "(Vaswani et al.)"
        title_clean = re.sub(r"\s*\([^)]*\)\s*", "", title_lower).strip()
        if title_clean and title_clean in context_lower:
            return True

        # Strip leading markers like "[Paper A] " from context
        context_clean = re.sub(r"\[.*?\]\s*", "", context_lower)
        if title_clean and title_clean in context_clean:
            return True

        # Fallback: require at least 3 significant tokens to match
        title_tokens = re.findall(r"[a-zA-Z0-9]{4,}", title_lower)
        if not title_tokens:
            return False

        required = max(3, len(title_tokens) // 2)
        match_count = 0
        for token in title_tokens:
            if token in context_lower:
                match_count += 1
                if match_count >= required:
                    return True
        return False
