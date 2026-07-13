"""Keyword analysis for user questions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.modules.copilot.retrieval.models import STOP_WORDS


@dataclass
class AnalyzedQuestion:
    """Keywords and signals extracted from a user question."""

    raw: str
    keywords: set[str] = field(default_factory=set)
    bigrams: set[str] = field(default_factory=set)
    phrases: list[str] = field(default_factory=list)
    methodology_signals: list[str] = field(default_factory=list)
    dataset_signals: list[str] = field(default_factory=list)
    technology_signals: list[str] = field(default_factory=list)
    domain_signals: list[str] = field(default_factory=list)
    author_signals: list[str] = field(default_factory=list)
    paper_title_signals: list[str] = field(default_factory=list)
    gap_signals: list[str] = field(default_factory=list)
    comparison_signals: bool = False
    how_why_signals: bool = False

    def has_signals(self) -> bool:
        return bool(
            self.keywords
            or self.bigrams
            or self.phrases
            or self.methodology_signals
            or self.dataset_signals
            or self.technology_signals
            or self.domain_signals
        )


class KeywordAnalyzer:
    """Extracts search signals from a user question using lightweight heuristics."""

    _METHODOLOGY_TRIGGERS = {
        "methodology",
        "method",
        "approach",
        "technique",
        "techniques",
        "algorithm",
        "framework",
        "pipeline",
        "architecture",
    }
    _DATASET_TRIGGERS = {
        "dataset",
        "datasets",
        "data",
        "benchmark",
        "benchmarks",
        "corpus",
        "collection",
        "database",
    }
    _TECHNOLOGY_TRIGGERS = {
        "technology",
        "technologies",
        "technique",
        "techniques",
        "tool",
        "tools",
        "library",
        "libraries",
        "platform",
        "platforms",
        "software",
        "framework",
        "implementation",
    }
    _DOMAIN_TRIGGERS = {
        "domain",
        "domains",
        "field",
        "fields",
        "area",
        "areas",
        "discipline",
        "application",
        "applications",
        "task",
        "tasks",
    }
    _AUTHOR_TRIGGERS = {
        "author",
        "authors",
        "who",
        "researcher",
        "researchers",
        "group",
        "team",
        "lab",
    }
    _PAPER_TRIGGERS = {
        "paper",
        "papers",
        "publication",
        "publications",
        "article",
        "articles",
        "study",
        "studies",
        "work",
        "research",
    }
    _GAP_TRIGGERS = {
        "gap",
        "gaps",
        "limitation",
        "limitations",
        "challenge",
        "challenges",
        "problem",
        "problems",
        "issue",
        "issues",
        "open",
        "missing",
        "lack",
        "future direction",
        "opportunity",
        "opportunities",
        "future work",
    }
    _COMPARISON_TRIGGERS = {
        "compare",
        "comparison",
        "difference",
        "differences",
        "versus",
        "vs",
        "similarity",
        "trade-off",
        "better",
        "worse",
    }
    _HOW_WHY_TRIGGERS = {"how", "why", "what causes", "what factors", "explain"}

    def analyze(self, question: str) -> AnalyzedQuestion:
        raw = question.strip().lower()
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-.#]*", raw)
        keywords = {t for t in tokens if len(t) > 1 and t not in STOP_WORDS}

        bigrams: set[str] = set()
        for i in range(len(tokens) - 1):
            bg = f"{tokens[i]} {tokens[i + 1]}"
            valid = (
                tokens[i] not in STOP_WORDS or tokens[i + 1] not in STOP_WORDS
            ) and bg not in STOP_WORDS
            if valid and len(bg) > 3:
                bigrams.add(bg)

        phrases = self._extract_phrases(raw)

        result = AnalyzedQuestion(
            raw=raw,
            keywords=keywords,
            bigrams=bigrams,
            phrases=phrases,
        )

        for keyword in keywords | bigrams | set(phrases):
            if keyword in self._METHODOLOGY_TRIGGERS or any(
                trigger in keyword for trigger in self._METHODOLOGY_TRIGGERS
            ):
                result.methodology_signals.append(keyword)
            if keyword in self._DATASET_TRIGGERS or any(
                trigger in keyword for trigger in self._DATASET_TRIGGERS
            ):
                result.dataset_signals.append(keyword)
            if keyword in self._TECHNOLOGY_TRIGGERS or any(
                trigger in keyword for trigger in self._TECHNOLOGY_TRIGGERS
            ):
                result.technology_signals.append(keyword)
            if keyword in self._DOMAIN_TRIGGERS or any(
                trigger in keyword for trigger in self._DOMAIN_TRIGGERS
            ):
                result.domain_signals.append(keyword)
            if keyword in self._AUTHOR_TRIGGERS:
                result.author_signals.append(keyword)
            if keyword in self._PAPER_TRIGGERS:
                result.paper_title_signals.append(keyword)
            if keyword in self._GAP_TRIGGERS or any(g in keyword for g in self._GAP_TRIGGERS):
                result.gap_signals.append(keyword)

        comparison_words = {t for t in tokens if t in self._COMPARISON_TRIGGERS}
        if comparison_words:
            result.comparison_signals = True

        how_why_words = {t for t in tokens if t in self._HOW_WHY_TRIGGERS}
        if how_why_words:
            result.how_why_signals = True

        return result

    @staticmethod
    def _extract_phrases(raw: str) -> list[str]:
        quoted = re.findall(r'"([^"]+)"', raw)
        return [q.strip().lower() for q in quoted if len(q.strip()) > 2]
