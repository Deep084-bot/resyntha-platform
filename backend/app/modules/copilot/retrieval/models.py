"""Shared models for the retrieval layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RetrievedSection:
    """A single knowledge section with its relevance score and source."""

    source: str  # e.g. "Knowledge Package", "Landscape", "Gap Report", "Paper Collection"
    label: str   # e.g. "Key Findings", "Methodologies", "Datasets"
    content: str
    score: float = 0.0
    char_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.content)


@dataclass
class RetrievalDiagnostics:
    """Internal diagnostics for a retrieval operation."""

    total_raw_sections: int = 0
    scored_sections: int = 0
    dedup_removed: int = 0
    selected_count: int = 0
    dropped_low_score: int = 0
    dropped_budget: int = 0
    truncated_count: int = 0
    used_fallback: bool = False
    total_char_count: int = 0
    budget_limit: int = 25000
    retrieval_duration_ms: float = 0.0
    num_keywords: int = 0
    num_signals: int = 0
    estimated_prompt_chars: int = 0
    retriever_type: str = "heuristic"
    detected_intent: str = ""
    aggregated_evidence_count: int = 0
    comparison_mode: bool = False
    reasoning_mode: bool = False
    grouped_citation_count: int = 0
    confidence_explanation: str = ""


@dataclass
class RetrievalResult:
    """Result of an investigation retrieval operation."""

    sections: list[RetrievedSection] = field(default_factory=list)
    metadata: list[str] = field(default_factory=list)
    total_char_count: int = 0
    truncated: bool = False
    diagnostics: RetrievalDiagnostics | None = None


STOP_WORDS: set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "and", "but",
    "or", "because", "about", "up", "down", "what", "which",
    "who", "whom", "this", "that", "these", "those", "it", "its",
    "please", "tell", "me", "about", "summarize", "explain",
    "describe", "list", "show", "give", "find", "what", "how",
}
