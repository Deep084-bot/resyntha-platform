"""Hybrid scoring — combines semantic similarity with keyword boosting."""

from __future__ import annotations

from app.modules.copilot.retrieval.analyzer import AnalyzedQuestion
from app.modules.copilot.retrieval.scorer import SectionScorer
from app.modules.copilot.retrieval.models import RetrievedSection

_SEMANTIC_WEIGHT = 0.7
_KEYWORD_WEIGHT = 0.3


class HybridScorer:
    """Combines semantic similarity with lightweight keyword boosting.

    The final hybrid score is::

        semantic_similarity * SEMANTIC_WEIGHT + keyword_boost * KEYWORD_WEIGHT
    """

    def __init__(self) -> None:
        self._scorer = SectionScorer()

    def score(
        self,
        section: RetrievedSection,
        question: AnalyzedQuestion,
        semantic_similarity: float,
    ) -> float:
        keyword_boost = self._scorer.score(section, question)
        keyword_normalized = min(keyword_boost / 100.0, 1.0)

        return (
            semantic_similarity * _SEMANTIC_WEIGHT +
            keyword_normalized * _KEYWORD_WEIGHT
        )
