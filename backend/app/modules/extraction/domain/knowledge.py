"""Domain schemas for knowledge extraction.

``ExtractionOutput`` is the structured result the LLM must return.
``PaperKnowledge`` wraps the output with paper metadata and provenance.
"""

import uuid

from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author extracted from a paper."""

    name: str = Field(description="Full author name")
    order: int | None = Field(
        default=None, description="Author position in the author list (1-based)"
    )
    is_corresponding: bool | None = Field(
        default=None, description="Whether this is the corresponding author"
    )


class Institution(BaseModel):
    """Affiliation extracted from a paper."""

    name: str = Field(description="Institution name")
    department: str | None = Field(default=None, description="Department or division")
    country: str | None = Field(default=None, description="Country of the institution")


class Dataset(BaseModel):
    """Dataset used or introduced in a paper."""

    name: str = Field(description="Dataset name")
    is_public: bool | None = Field(
        default=None, description="Whether the dataset is publicly available"
    )
    is_benchmark: bool | None = Field(
        default=None, description="Whether this is a benchmark dataset"
    )


class Technology(BaseModel):
    """Technology (framework, model, algorithm, library) used in a paper."""

    name: str = Field(description="Technology name")
    type: str | None = Field(
        default=None, description="Category: framework, model, algorithm, library"
    )


class Metric(BaseModel):
    """Evaluation metric reported in a paper."""

    name: str = Field(description="Metric name (e.g. accuracy, F1, BLEU)")
    value: str | None = Field(default=None, description="Reported value")
    dataset: str | None = Field(
        default=None, description="Dataset on which the metric was measured"
    )


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
        description="Primary research methodology or approach used",
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

    # ── New structured fields ──────────────────────────────────────

    authors: list[Author] = Field(
        default_factory=list,
        description="List of authors with names, order, and corresponding flag",
    )
    institutions: list[Institution] = Field(
        default_factory=list,
        description="List of affiliations with institution, department, country",
    )
    datasets_used: list[Dataset] = Field(
        default_factory=list,
        description="Datasets used or introduced, with public/benchmark flags",
    )
    technologies: list[Technology] = Field(
        default_factory=list,
        description="Frameworks, models, algorithms, libraries used",
    )
    evaluation_metrics: list[Metric] = Field(
        default_factory=list,
        description="Evaluation metrics with reported values and datasets",
    )
    research_domains: list[str] = Field(
        default_factory=list,
        description="Research domains or subfields the paper belongs to",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords or key phrases describing the paper",
    )
    paper_type: str | None = Field(
        default=None,
        description="Type of paper: survey, benchmark, application, theory, etc.",
    )
    funding: str | None = Field(
        default=None,
        description="Funding information or grant acknowledgments",
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
