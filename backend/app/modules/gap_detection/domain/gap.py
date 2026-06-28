"""Domain models for gap detection.

``Gap`` represents a single detected gap or opportunity.
``ResearchGapReport`` wraps all detected gaps with metadata.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class GapCategory(StrEnum):
    """Categories of research gaps that the engine can detect."""

    DATASET = "dataset"
    METHODOLOGY = "methodology"
    EVALUATION = "evaluation"
    FUTURE_WORK = "future_work"
    LIMITATION = "limitation"
    METHOD_COMBINATION = "method_combination"
    TEMPORAL = "temporal"


class GapSeverity(StrEnum):
    """Relative importance of a detected gap."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """Supporting evidence for a detected gap."""

    description: str = ""
    supporting_paper_ids: list[str] = Field(default_factory=list)
    supporting_facts: list[str] = Field(default_factory=list)
    statistics: dict[str, float | int] = Field(default_factory=dict)


class Gap(BaseModel):
    """A single detected research gap or opportunity."""

    id: str = ""
    title: str = ""
    description: str = ""
    category: GapCategory = GapCategory.METHODOLOGY
    confidence: float = 0.0
    severity: GapSeverity = GapSeverity.MEDIUM
    evidence: Evidence = Field(default_factory=Evidence)
    recommendation: str = ""


class GapSummary(BaseModel):
    """Aggregated summary of the gap detection run."""

    total_gaps: int = 0
    high_confidence_gaps: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    severities: dict[str, int] = Field(default_factory=dict)


class ResearchGapReport(BaseModel):
    """Complete gap detection report for an investigation."""

    summary: GapSummary = Field(default_factory=GapSummary)
    gaps: list[Gap] = Field(default_factory=list)
    statistics: dict[str, float | int] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: str = ""
