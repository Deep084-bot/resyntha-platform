"""Investigation retriever — orchestrates section extraction, scoring, and selection."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
from app.modules.copilot.retrieval.extractor import SectionExtractor
from app.modules.copilot.retrieval.models import (
    RetrievalDiagnostics,
    RetrievalResult,
    RetrievedSection,
)
from app.modules.copilot.retrieval.scorer import SectionScorer
from app.observability.logger import get_logger

logger = get_logger(__name__)

_MAX_CONTEXT_CHARS = 25000
_MIN_SECTION_CHARS = 30
_FALLBACK_CHARS = 8000


class InvestigationRetriever:
    """Orchestrates context retrieval for the Copilot.

    1. Extracts logical sections from investigation artifacts.
    2. Analyses the user question for keywords and signals.
    3. Scores and ranks sections by relevance.
    4. Deduplicates overlapping information.
    5. Selects top sections within the token budget.
    6. Falls back to a broad summary when nothing matches.
    7. Tracks internal diagnostics.
    """

    def __init__(self, session: Session) -> None:
        self._extractor = SectionExtractor(session)
        self._analyzer = KeywordAnalyzer()
        self._scorer = SectionScorer()

    def retrieve(
        self,
        investigation_id: uuid.UUID,
        question: str,
        max_chars: int = _MAX_CONTEXT_CHARS,
    ) -> RetrievalResult:
        start = time.perf_counter()

        analyzed = self._analyzer.analyze(question)
        all_sections = self._extractor.extract_all(investigation_id)

        diag = RetrievalDiagnostics(
            total_raw_sections=len(all_sections),
            budget_limit=max_chars,
            num_keywords=len(analyzed.keywords),
            num_signals=sum([
                1 for s in [
                    analyzed.methodology_signals, analyzed.dataset_signals,
                    analyzed.technology_signals, analyzed.domain_signals,
                    analyzed.author_signals, analyzed.gap_signals,
                ] if s
            ]),
        )

        if not all_sections:
            diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(
                metadata=["No sections found in investigation artifacts."],
                diagnostics=diag,
            )

        scored = self._score_and_sort(all_sections, analyzed)
        diag.scored_sections = len(scored)

        deduped, dedup_removed = self._deduplicate(scored)
        diag.dedup_removed = dedup_removed

        selected, meta, stats = self._select_within_budget(deduped, max_chars)
        diag.selected_count = len(selected)
        diag.dropped_low_score = stats.get("dropped_low_score", 0)
        diag.dropped_budget = stats.get("dropped_budget", 0)
        diag.truncated_count = stats.get("truncated_count", 0)
        diag.used_fallback = stats.get("used_fallback", False)
        diag.total_char_count = sum(s.char_count for s in selected)

        diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000

        return RetrievalResult(
            sections=selected,
            metadata=meta,
            total_char_count=diag.total_char_count,
            truncated=diag.total_char_count > max_chars,
            diagnostics=diag,
        )

    # ── Scoring and ranking ─────────────────────────────────────

    def _score_and_sort(
        self,
        sections: list[RetrievedSection],
        analyzed,
    ) -> list[RetrievedSection]:
        for section in sections:
            section.score = self._scorer.score(section, analyzed)
        return sorted(sections, key=lambda s: s.score, reverse=True)

    # ── Duplicate elimination ───────────────────────────────────

    @staticmethod
    def _deduplicate(sections: list[RetrievedSection]) -> tuple[list[RetrievedSection], int]:
        """Remove near-duplicate content across sections.

        Strategy: if two sections share the same label AND have content
        that overlaps significantly, keep only the one with the higher score.

        Returns (deduplicated list, number removed).
        """
        if not sections:
            return sections, 0

        seen: list[RetrievedSection] = []
        for section in sections:
            is_dup = False
            for existing in seen:
                if section.label == existing.label and section.source != existing.source:
                    overlap = InvestigationRetriever._content_overlap(
                        section.content, existing.content
                    )
                    if overlap > 0.65:
                        is_dup = True
                        break
            if not is_dup:
                seen.append(section)
        return seen, len(sections) - len(seen)

    @staticmethod
    def _content_overlap(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        return len(intersection) / min(len(set_a), len(set_b))

    # ── Budget selection ────────────────────────────────────────

    def _select_within_budget(
        self,
        sections: list[RetrievedSection],
        max_chars: int,
    ) -> tuple[list[RetrievedSection], list[str], dict[str, int | bool]]:
        meta: list[str] = []
        selected: list[RetrievedSection] = []
        remaining = max_chars
        stats: dict[str, int | bool] = {
            "dropped_low_score": 0,
            "dropped_budget": 0,
            "truncated_count": 0,
            "used_fallback": False,
        }

        if not sections:
            return selected, meta, stats

        has_positive_score = any(s.score > 0 for s in sections)

        for section in sections:
            if section.score <= 0 and has_positive_score:
                stats["dropped_low_score"] = int(stats["dropped_low_score"]) + 1
                continue
            if section.char_count < _MIN_SECTION_CHARS and section.score <= 0:
                stats["dropped_low_score"] = int(stats["dropped_low_score"]) + 1
                continue
            if section.char_count <= remaining:
                selected.append(section)
                remaining -= section.char_count
                meta.append(
                    f"{section.source} → {section.label} "
                    f"(score={section.score:.1f}, chars={section.char_count})"
                )
            else:
                if not selected:
                    truncated = RetrievedSection(
                        source=section.source,
                        label=section.label,
                        content=section.content[:remaining],
                        score=section.score,
                    )
                    selected.append(truncated)
                    stats["truncated_count"] = int(stats["truncated_count"]) + 1
                    meta.append(
                        f"{section.source} → {section.label} "
                        f"(score={section.score:.1f}, TRUNCATED)"
                    )
                else:
                    stats["dropped_budget"] = int(stats["dropped_budget"]) + 1
                    meta.append(
                        f"{section.source} → {section.label} "
                        f"(score={section.score:.1f}, SKIPPED - over budget)"
                    )

        if not selected:
            meta.append("No relevant sections found; using fallback.")
            stats["used_fallback"] = True
            fallback = self._build_fallback(sections)
            if fallback:
                selected.append(fallback)

        return selected, meta, stats

    @staticmethod
    def _build_fallback(sections: list[RetrievedSection]) -> RetrievedSection | None:
        """Build a broad summary from the highest-ranked sections when nothing matched."""
        if not sections:
            return None
        total = 0
        parts: list[str] = []
        for section in sections[:5]:
            limit = _FALLBACK_CHARS - total
            if limit <= 0:
                break
            chunk = section.content[:limit]
            parts.append(f"[{section.source} / {section.label}]\n{chunk}")
            total += len(chunk)

        if not parts:
            return None

        return RetrievedSection(
            source="Investigation Summary",
            label="Overview",
            content="\n\n".join(parts),
            score=0.0,
        )
