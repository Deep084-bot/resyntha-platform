"""Question classification models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QuestionIntent(str, Enum):
    PAPER_SUMMARY = "paper_summary"
    PAPER_COMPARISON = "paper_comparison"
    METHODOLOGY_COMPARISON = "methodology_comparison"
    DATASET_COMPARISON = "dataset_comparison"
    TECHNOLOGY_COMPARISON = "technology_comparison"
    LIMITATION_ANALYSIS = "limitation_analysis"
    RESEARCH_GAP_EXPLORATION = "research_gap_exploration"
    TREND_ANALYSIS = "trend_analysis"
    EVIDENCE_LOOKUP = "evidence_lookup"
    GENERAL_RESEARCH_QUESTION = "general_research_question"


@dataclass
class QuestionAnalysis:
    """Output of the question classifier."""

    intent: QuestionIntent
    raw: str
    paper_mentions: list[str] = field(default_factory=list)
    comparison_targets: list[str] = field(default_factory=list)
    is_comparison: bool = False
    confidence: float = 1.0
