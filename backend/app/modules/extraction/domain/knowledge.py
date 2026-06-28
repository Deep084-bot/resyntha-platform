"""Domain schemas for knowledge extraction.

``ExtractionOutput`` is the structured result the LLM must return.
``PaperKnowledge`` wraps the output with paper metadata and provenance.
"""

import uuid

from pydantic import BaseModel, Field


class ExtractionOutput(BaseModel):
    """Structured knowledge extracted from a single paper."""

    research_questions: list[str] = Field(
        default_factory=list,
        description="Key research questions the paper addresses",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Main findings or results reported in the paper",
    )
    methodology: str | None = Field(
        default=None,
        description="Research methodology or approach used",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Limitations acknowledged by the authors",
    )
    key_contributions: list[str] = Field(
        default_factory=list,
        description="Novel contributions of the paper",
    )
    relevant_techniques: list[str] = Field(
        default_factory=list,
        description="Methods, tools, or techniques used or introduced",
    )
    cited_works: list[str] = Field(
        default_factory=list,
        description="Important works cited by the paper",
    )
    future_work: list[str] = Field(
        default_factory=list,
        description="Future research directions suggested by the authors",
    )
    summary: str = Field(
        default="",
        description="Concise one-paragraph summary of the paper",
    )


class PaperKnowledge(BaseModel):
    """Complete knowledge extraction result for one paper."""

    paper_id: uuid.UUID
    paper_title: str
    extraction: ExtractionOutput
    model_used: str
    tokens_used: int | None = None
    confidence_score: float | None = None
    extracted_at: str = ""
