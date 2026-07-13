"""Lightweight deterministic question classifier.

Maps user questions into one of ten research intents using keyword and
pattern matching.  No LLM calls, no external dependencies beyond the
standard library.
"""

from __future__ import annotations

import re

from app.modules.copilot.classification.models import QuestionAnalysis, QuestionIntent


class QuestionClassifier:
    """Classifies a user question into a research intent.

    Strategy (in priority order):
      1. Detect paper-comparison patterns (quotations + compare language)
      2. Detect methodology/dataset/technology comparisons
      3. Detect paper-summary patterns
      4. Detect limitation / gap questions
      5. Detect trend questions
      6. Detect evidence-lookup questions
      7. Fallback → GENERAL_RESEARCH_QUESTION
    """

    _COMPARE_WORDS = {
        "compare",
        "comparison",
        "differences",
        "versus",
        "vs",
        "similarities",
        "better",
        "worse",
        "best",
        "advantages",
        "disadvantages",
    }
    _PAPER_WORDS = {
        "paper",
        "papers",
        "publication",
        "publications",
        "article",
        "articles",
        "study",
        "studies",
    }
    _METHODOLOGY_WORDS = {
        "methodology",
        "methodologies",
        "method",
        "methods",
        "approach",
        "approaches",
        "technique",
        "techniques",
        "algorithm",
        "algorithms",
        "framework",
        "frameworks",
        "pipeline",
        "pipelines",
        "architecture",
        "architectures",
    }
    _DATASET_WORDS = {
        "dataset",
        "datasets",
        "benchmark",
        "benchmarks",
        "corpus",
        "corpora",
        "database",
        "databases",
    }
    _TECHNOLOGY_WORDS = {
        "technology",
        "technologies",
        "tool",
        "tools",
        "library",
        "libraries",
        "platform",
        "platforms",
        "software",
        "implementation",
        "implementations",
        "model",
        "models",
        "framework",
        "frameworks",
    }
    _GAP_WORDS = {
        "gap",
        "gaps",
        "limitation",
        "limitations",
        "drawback",
        "drawbacks",
        "weakness",
        "weaknesses",
        "challenge",
        "challenges",
        "problem",
        "problems",
        "issue",
        "issues",
        "unexplored",
        "missing",
        "lack",
        "opportunity",
        "opportunities",
    }
    _GAP_FUTURE_PHRASES = [
        "future work",
        "future direction",
        "future research",
        "what future",
        "open problem",
        "open question",
        "unexplored",
    ]
    _TREND_PHRASES = [
        "trends",
        "trending",
        "state of the art",
        "emerging",
        "recent advances",
        "latest",
        "research directions",
        "evolution of",
    ]

    _PAPER_MENTION_PATTERN = re.compile(r'"([^"]+)"')
    _COMPARISON_TARGET_PATTERN = re.compile(
        r"(?:compare|between)\s+(.+?)\s+and\s+(.+?)(?:\?|$|\.)", re.IGNORECASE
    )

    @staticmethod
    def _has_any(phrases: list[str], raw: str) -> bool:
        return any(p in raw for p in phrases)

    @staticmethod
    def _has_set(word_set: set[str], tokens: set[str]) -> bool:
        return bool(tokens & word_set)

    def classify(self, question: str) -> QuestionAnalysis:
        raw = question.strip().lower()
        tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_\-.#]*", raw))
        paper_mentions = self._extract_paper_mentions(question)
        comparison_targets = self._extract_comparison_targets(question)

        is_compare = bool(tokens & self._COMPARE_WORDS) or len(comparison_targets) > 0

        # -- Comparison intents --
        if is_compare:
            if paper_mentions or (
                len(comparison_targets) >= 2 and self._has_set(self._PAPER_WORDS, tokens)
            ):
                return QuestionAnalysis(
                    intent=QuestionIntent.PAPER_COMPARISON,
                    raw=raw,
                    paper_mentions=paper_mentions,
                    comparison_targets=comparison_targets,
                    is_comparison=True,
                )
            if self._has_set(self._TECHNOLOGY_WORDS, tokens):
                return QuestionAnalysis(
                    intent=QuestionIntent.TECHNOLOGY_COMPARISON,
                    raw=raw,
                    comparison_targets=comparison_targets,
                    is_comparison=True,
                )
            if self._has_set(self._METHODOLOGY_WORDS, tokens):
                return QuestionAnalysis(
                    intent=QuestionIntent.METHODOLOGY_COMPARISON,
                    raw=raw,
                    comparison_targets=comparison_targets,
                    is_comparison=True,
                )
            if self._has_set(self._DATASET_WORDS, tokens):
                return QuestionAnalysis(
                    intent=QuestionIntent.DATASET_COMPARISON,
                    raw=raw,
                    comparison_targets=comparison_targets,
                    is_comparison=True,
                )

        # Also handle "which X is most" implicit comparisons
        _implicit_compare_pattern = re.compile(
            r"\bwhich\s+(.+?)\s+(?:is|are)\s+most", re.IGNORECASE
        )
        implicit_match = _implicit_compare_pattern.search(raw)
        if implicit_match:
            target = implicit_match.group(1).strip().lower()
            if target in self._METHODOLOGY_WORDS or any(
                w in target for w in self._METHODOLOGY_WORDS if len(w) > 4
            ):
                return QuestionAnalysis(
                    intent=QuestionIntent.METHODOLOGY_COMPARISON, raw=raw, is_comparison=True
                )
            if target in self._DATASET_WORDS or any(
                w in target for w in self._DATASET_WORDS if len(w) > 4
            ):
                return QuestionAnalysis(
                    intent=QuestionIntent.DATASET_COMPARISON, raw=raw, is_comparison=True
                )
            if target in self._TECHNOLOGY_WORDS or any(
                w in target for w in self._TECHNOLOGY_WORDS if len(w) > 4
            ):
                return QuestionAnalysis(
                    intent=QuestionIntent.TECHNOLOGY_COMPARISON, raw=raw, is_comparison=True
                )

        # -- Paper summary --
        if paper_mentions:
            summary_words = ("summarize", "summarise", "summary", "what does", "tell me about")
            if any(w in raw for w in summary_words) or not self._has_set(
                self._METHODOLOGY_WORDS
                | self._DATASET_WORDS
                | self._TECHNOLOGY_WORDS
                | self._GAP_WORDS,
                tokens,
            ):
                return QuestionAnalysis(
                    intent=QuestionIntent.PAPER_SUMMARY,
                    raw=raw,
                    paper_mentions=paper_mentions,
                )

        # -- Limitation / Gap --
        has_gap = self._has_set(self._GAP_WORDS, tokens)
        limitation_substrings = ("limitation", "drawback", "weakness", "downside")
        if has_gap and any(w in raw for w in limitation_substrings):
            return QuestionAnalysis(intent=QuestionIntent.LIMITATION_ANALYSIS, raw=raw)
        if has_gap or self._has_any(self._GAP_FUTURE_PHRASES, raw):
            return QuestionAnalysis(intent=QuestionIntent.RESEARCH_GAP_EXPLORATION, raw=raw)

        # -- Trend --
        if self._has_any(self._TREND_PHRASES, raw):
            return QuestionAnalysis(intent=QuestionIntent.TREND_ANALYSIS, raw=raw)

        # -- Evidence lookup --
        evidence_phrases = (
            "what is ",
            "what are ",
            "define ",
            "explain ",
            "find evidence",
            "show me",
            "tell me about",
            "describe ",
            "give me",
            "list ",
        )
        if any(w in raw for w in evidence_phrases):
            return QuestionAnalysis(intent=QuestionIntent.EVIDENCE_LOOKUP, raw=raw)

        return QuestionAnalysis(intent=QuestionIntent.GENERAL_RESEARCH_QUESTION, raw=raw)

    @staticmethod
    def _extract_paper_mentions(question: str) -> list[str]:
        return [
            m.group(1).strip() for m in QuestionClassifier._PAPER_MENTION_PATTERN.finditer(question)
        ]

    @staticmethod
    def _extract_comparison_targets(question: str) -> list[str]:
        targets: list[str] = []
        for m in QuestionClassifier._COMPARISON_TARGET_PATTERN.finditer(question):
            t1 = m.group(1).strip().strip('"')
            t2 = m.group(2).strip().strip('"')
            if t1:
                targets.append(t1)
            if t2:
                targets.append(t2)
        return targets
