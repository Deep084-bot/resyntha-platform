"""Heuristic section scoring based on keyword overlap and signal matching."""

from __future__ import annotations

import re

from app.modules.copilot.retrieval.analyzer import AnalyzedQuestion
from app.modules.copilot.retrieval.models import RetrievedSection


class SectionScorer:
    """Scores retrieved sections against an analysed question using lightweight heuristics.

    Signals and their weights:
        - Keyword overlap in content      10 pts/match
        - Bigram overlap in content       15 pts/match
        - Exact quoted phrase match      100 pts
        - Section label match             30 pts
        - Methodology signal match        12 pts
        - Dataset signal match            12 pts
        - Technology signal match         12 pts
        - Domain signal match             12 pts
        - Author signal match             12 pts
        - Paper title match               15 pts
        - Gap signal match                20 pts
    """

    _LABEL_ALIASES: dict[str, list[str]] = {
        "key findings": ["finding", "result", "discovery", "outcome"],
        "methodologies": ["methodology", "method", "approach", "technique", "algorithm"],
        "technologies": ["technology", "tool", "software", "library", "framework"],
        "datasets": ["dataset", "data", "benchmark", "corpus"],
        "limitations": ["limitation", "weakness", "drawback", "constraint", "challenge"],
        "future work": ["future", "direction", "next step", "open problem"],
        "research questions": ["question", "research question"],
        "research domains": ["domain", "field", "area", "discipline"],
        "authors": ["author", "researcher"],
        "evaluation metrics": ["metric", "evaluation", "performance"],
        "research gaps": ["gap", "missing", "open"],
        "recommendations": ["recommendation", "suggestion", "proposal"],
        "applications": ["application", "use case"],
    }

    def score(self, section: RetrievedSection, question: AnalyzedQuestion) -> float:
        score = 0.0
        content_lower = section.content.lower()
        label_lower = section.label.lower()

        score += self._keyword_overlap(content_lower, question.keywords, weight=10.0)
        score += self._bigram_overlap(content_lower, question.bigrams, weight=15.0)
        score += self._phrase_match(content_lower, question.phrases, weight=100.0)
        score += self._label_match(label_lower, question, weight=30.0)
        score += self._signal_matches(content_lower, question)

        return score

    def _keyword_overlap(self, text: str, keywords: set[str], weight: float) -> float:
        count = 0
        for kw in keywords:
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            matches = pattern.findall(text)
            count += len(matches)
        return count * weight

    def _bigram_overlap(self, text: str, bigrams: set[str], weight: float) -> float:
        count = 0
        for bg in bigrams:
            if bg in text:
                count += text.count(bg)
        return count * weight

    def _phrase_match(self, text: str, phrases: list[str], weight: float) -> float:
        count = 0
        for phrase in phrases:
            if phrase in text:
                count += 1
        return count * weight

    def _label_match(self, label: str, question: AnalyzedQuestion, weight: float) -> float:
        aliases = self._LABEL_ALIASES.get(label, [])
        all_terms = [label] + aliases
        count = 0
        for term in all_terms:
            if term in question.keywords or term in question.bigrams:
                count += 1
        return count * weight

    def _signal_matches(self, text: str, question: AnalyzedQuestion) -> float:
        score = 0.0
        text_lower = text.lower()

        if question.methodology_signals:
            score += self._count_term_matches(text_lower, question.methodology_signals) * 12.0
        if question.dataset_signals:
            score += self._count_term_matches(text_lower, question.dataset_signals) * 12.0
        if question.technology_signals:
            score += self._count_term_matches(text_lower, question.technology_signals) * 12.0
        if question.domain_signals:
            score += self._count_term_matches(text_lower, question.domain_signals) * 12.0
        if question.author_signals:
            score += self._count_term_matches(text_lower, question.author_signals) * 12.0
        if question.gap_signals:
            score += len(question.gap_signals) * 20.0

        return score

    @staticmethod
    def _count_term_matches(text: str, signals: list[str]) -> int:
        count = 0
        for signal in signals:
            if signal in text:
                count += 1
        return count
