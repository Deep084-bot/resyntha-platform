"""Evidence aggregation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupportingPaper:
    """A paper supporting a specific piece of evidence."""

    title: str
    relevance: str = ""
    confidence: float = 0.0


@dataclass
class SourceChunk:
    """Original chunk that contributed to this evidence."""

    source: str
    label: str
    content: str
    score: float = 0.0


@dataclass
class EvidenceItem:
    """A single piece of structured evidence derived from retrieved chunks."""

    claim: str
    supporting_papers: list[SupportingPaper] = field(default_factory=list)
    source_chunks: list[SourceChunk] = field(default_factory=list)
    confidence: float = 0.0
    is_inference: bool = False
    claim_group: str = ""


@dataclass
class EvidenceBundle:
    """Structured evidence output from the EvidenceAggregator.

    Groups evidence by claim, tracks provenance and confidence.
    """

    items: list[EvidenceItem] = field(default_factory=list)
    total_sources: int = 0
    total_papers: set[str] = field(default_factory=set)
    aggregated_char_count: int = 0
    compression_ratio: float = 0.0


@dataclass
class GroupedCitation:
    """A citation grouped under a specific claim."""

    claim: str
    papers: list[SupportingPaper] = field(default_factory=list)


@dataclass
class ComparisonItem:
    """A structured comparison between two or more targets."""

    aspect: str
    targets: dict[str, str] = field(default_factory=dict)  # target -> evidence
    papers: list[SupportingPaper] = field(default_factory=list)
