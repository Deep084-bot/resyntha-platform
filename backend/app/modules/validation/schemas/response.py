"""Response schemas for the Validation API."""

from pydantic import BaseModel


class ValidationSummary(BaseModel):
    """Aggregated validation statistics for a set of papers."""

    total_papers: int
    valid: int
    warning: int
    invalid: int
    duplicates: int
    average_score: float
    timestamp: str


class ValidationResultResponse(BaseModel):
    """Full result of a validation run."""

    summary: ValidationSummary
    validated_papers: list[dict]
