"""Semantic investigation retriever using pgvector and hybrid scoring."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.modules.copilot.classification.models import QuestionIntent
from app.modules.copilot.embeddings.base import EmbeddingProvider
from app.modules.copilot.embeddings.factory import create_embedding_provider
from app.modules.copilot.retrieval.analyzer import KeywordAnalyzer
from app.modules.copilot.retrieval.compression import ContextCompressor
from app.modules.copilot.retrieval.hybrid import HybridScorer
from app.modules.copilot.retrieval.models import (
    RetrievalDiagnostics,
    RetrievalResult,
    RetrievedSection,
)
from app.modules.copilot.vector.repository import VectorRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)

_MAX_CONTEXT_CHARS = 25000
_MIN_SECTION_CHARS = 30
_FALLBACK_CHARS = 8000

_INTENT_STRATEGIES: dict[QuestionIntent, dict] = {
    QuestionIntent.PAPER_SUMMARY: {
        "top_k": 30,
        "priority_labels": {"Key Findings", "Summary", "Research Questions"},
    },
    QuestionIntent.PAPER_COMPARISON: {
        "top_k": 40,
        "priority_sources": {"Knowledge Package"},
    },
    QuestionIntent.METHODOLOGY_COMPARISON: {
        "top_k": 30,
        "priority_labels": {"Methodologies"},
    },
    QuestionIntent.DATASET_COMPARISON: {
        "top_k": 30,
        "priority_labels": {"Datasets", "Evaluation Metrics"},
    },
    QuestionIntent.TECHNOLOGY_COMPARISON: {
        "top_k": 30,
        "priority_labels": {"Technologies"},
    },
    QuestionIntent.LIMITATION_ANALYSIS: {
        "top_k": 25,
        "priority_labels": {"Limitations", "Future Work"},
    },
    QuestionIntent.RESEARCH_GAP_EXPLORATION: {
        "top_k": 25,
        "priority_sources": {"Gap Report", "Research Gap Report"},
        "priority_labels": {"Research Gaps", "Recommendations", "Limitations", "Future Work"},
    },
    QuestionIntent.TREND_ANALYSIS: {
        "top_k": 30,
        "priority_sources": {"Landscape", "Research Landscape"},
    },
    QuestionIntent.EVIDENCE_LOOKUP: {
        "top_k": 25,
        "priority_sources": {"Knowledge Package"},
    },
    QuestionIntent.GENERAL_RESEARCH_QUESTION: {
        "top_k": 20,
    },
}

_PRIORITY_BOOST = 0.25


class SemanticRetriever:
    """Replaces heuristic keyword retrieval with semantic search + hybrid scoring.

    Workflow:
    1. Embed the user question.
    2. Vector search for top-k chunks.
    3. Hybrid score (semantic + keyword boost).
    4. Context compression (deduplicate overlapping chunks).
    5. Budget selection → RetrievalResult.
    """

    def __init__(
        self,
        session: Session,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._vector_repo = VectorRepository(session)
        self._analyzer = KeywordAnalyzer()
        self._hybrid = HybridScorer()
        self._compressor = ContextCompressor()
        if embedder is not None:
            self._embedder = embedder
        else:
            self._embedder = create_embedding_provider("local")

    def retrieve(
        self,
        investigation_id: uuid.UUID,
        question: str,
        max_chars: int = _MAX_CONTEXT_CHARS,
        top_k: int = 20,
        intent: QuestionIntent | None = None,
    ) -> RetrievalResult:
        start = time.perf_counter()
        diag = RetrievalDiagnostics(budget_limit=max_chars, retriever_type="semantic")

        analyzed = self._analyzer.analyze(question)
        diag.num_keywords = len(analyzed.keywords)
        diag.num_signals = sum([
            1 for s in [
                analyzed.methodology_signals, analyzed.dataset_signals,
                analyzed.technology_signals, analyzed.domain_signals,
                analyzed.author_signals, analyzed.gap_signals,
            ] if s
        ])

        diag.detected_intent = intent.value if intent else ""

        # Compute intent-aware strategy
        strategy = _INTENT_STRATEGIES.get(intent, _INTENT_STRATEGIES[QuestionIntent.GENERAL_RESEARCH_QUESTION])
        effective_top_k = strategy.get("top_k", top_k)
        priority_labels: set[str] = strategy.get("priority_labels", set())
        priority_sources: set[str] = strategy.get("priority_sources", set())

        # If no embeddings exist, return empty result (caller should fall back)
        if not self._vector_repo.has_embeddings(investigation_id):
            diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(
                metadata=["No embeddings found for this investigation."],
                diagnostics=diag,
            )

        # Embed the question
        embed_start = time.perf_counter()
        try:
            query_vec = self._embedder.embed_query(question)
        except Exception as exc:
            logger.error("semantic_retriever_embed_error", error=str(exc)[:500])
            diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(
                metadata=["Failed to embed question."],
                diagnostics=diag,
            )
        diag.retrieval_duration_ms = (time.perf_counter() - embed_start) * 1000

        # Vector search (with intent-adjusted top_k)
        search_start = time.perf_counter()
        try:
            results = self._vector_repo.search(
                investigation_id, query_vec, top_k=effective_top_k,
            )
        except Exception as exc:
            logger.error("semantic_retriever_search_error", error=str(exc)[:500])
            diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(
                metadata=["Vector search failed."],
                diagnostics=diag,
            )
        search_latency = (time.perf_counter() - search_start) * 1000

        if not results:
            diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(
                metadata=["No relevant chunks found via semantic search."],
                diagnostics=diag,
            )

        # Convert to RetrievedSections with hybrid scores + intent boost
        hybrid_start = time.perf_counter()
        sections: list[RetrievedSection] = []
        for chunk_emb, similarity in results:
            section = RetrievedSection(
                source=chunk_emb.source,
                label=chunk_emb.section,
                content=chunk_emb.content,
            )
            hybrid_score = self._hybrid.score(section, analyzed, similarity)
            if (priority_labels and section.label in priority_labels) or \
               (priority_sources and section.source in priority_sources):
                hybrid_score = min(hybrid_score + _PRIORITY_BOOST, 1.0)
            section.score = hybrid_score
            sections.append(section)
        sections.sort(key=lambda s: s.score, reverse=True)
        diag.scored_sections = len(sections)

        # Context compression
        compressed = self._compressor.compress(sections)
        diag.dedup_removed = len(sections) - len(compressed)

        # Budget selection
        selected, meta, stats = self._select_within_budget(compressed, max_chars)
        diag.selected_count = len(selected)
        diag.dropped_budget = int(stats["dropped_budget"])
        diag.truncated_count = int(stats["truncated_count"])
        diag.used_fallback = bool(stats["used_fallback"])
        diag.total_char_count = sum(s.char_count for s in selected)

        diag.retrieval_duration_ms = (time.perf_counter() - start) * 1000
        diag.total_raw_sections = len(results)

        return RetrievalResult(
            sections=selected,
            metadata=meta,
            total_char_count=diag.total_char_count,
            truncated=diag.total_char_count > max_chars,
            diagnostics=diag,
        )

    # ── Budget selection (shared with InvestigationRetriever) ───

    def _select_within_budget(
        self,
        sections: list[RetrievedSection],
        max_chars: int,
    ) -> tuple[list[RetrievedSection], list[str], dict[str, int | bool]]:
        meta: list[str] = []
        selected: list[RetrievedSection] = []
        remaining = max_chars
        stats: dict[str, int | bool] = {
            "dropped_budget": 0,
            "truncated_count": 0,
            "used_fallback": False,
        }

        if not sections:
            return selected, meta, stats

        for section in sections:
            if section.char_count < _MIN_SECTION_CHARS and section.score == 0.0:
                continue
            if section.char_count <= remaining:
                selected.append(section)
                remaining -= section.char_count
                meta.append(
                    f"{section.source} → {section.label} "
                    f"(score={section.score:.2f}, chars={section.char_count})"
                )
            elif not selected:
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
                    f"(score={section.score:.2f}, TRUNCATED)"
                )
            else:
                stats["dropped_budget"] = int(stats["dropped_budget"]) + 1
                meta.append(
                    f"{section.source} → {section.label} "
                    f"(score={section.score:.2f}, SKIPPED - over budget)"
                )

        if not selected:
            meta.append("No sections within budget; using fallback.")
            stats["used_fallback"] = True
            fallback = self._build_fallback(sections)
            if fallback:
                selected.append(fallback)

        return selected, meta, stats

    @staticmethod
    def _build_fallback(sections: list[RetrievedSection]) -> RetrievedSection | None:
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
