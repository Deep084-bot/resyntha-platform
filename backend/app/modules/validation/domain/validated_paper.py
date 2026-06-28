"""Validated paper domain model."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.modules.retrieval.domain.paper import Paper


class ValidationStatus(str, Enum):
    """Outcome of validating a single paper."""

    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class ValidationIssue(BaseModel):
    """A single validation finding."""

    rule: str
    message: str
    severity: str  # "error" or "warning"


class ValidatedPaper(BaseModel):
    """A paper together with its validation results."""

    paper: dict[str, Any]
    validation_status: ValidationStatus
    validation_messages: list[str]
    validation_score: int
    validation_timestamp: str
