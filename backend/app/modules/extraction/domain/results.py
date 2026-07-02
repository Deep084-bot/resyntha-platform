"""Extraction result models.

``ExtractionBatchResult`` aggregates per-paper outcomes so the pipeline
stage can determine its status from the statistics rather than silently
dropping failures.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel

from app.modules.extraction.domain.models import ExtractedKnowledge


class FailureReason(str, Enum):
    """Why a single paper extraction did not succeed."""

    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    MALFORMED_JSON = "malformed_json"
    VALIDATION_ERROR = "validation_error"
    API_ERROR = "api_error"
    UNKNOWN = "unknown"


class ExtractionFailure(BaseModel):
    """A single paper extraction that did not succeed."""

    paper_id: uuid.UUID
    title: str
    reason: FailureReason
    detail: str | None = None


class ExtractionStats(BaseModel):
    """Aggregate statistics for one extraction batch run."""

    total: int
    successful: int
    failed: int
    provider: str
    failure_reasons: dict[str, int] = {}
    duration_seconds: float | None = None


@dataclass
class ExtractionBatchResult:
    """Complete outcome of an extraction run across all papers."""

    knowledge: list[ExtractedKnowledge] = field(default_factory=list)
    failures: list[ExtractionFailure] = field(default_factory=list)
    stats: ExtractionStats | None = None
