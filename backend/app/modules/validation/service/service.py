"""Validation service — orchestrates all validators and produces
validated paper results."""

from datetime import datetime, timezone

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import (
    ValidatedPaper,
    ValidationIssue,
    ValidationStatus,
)
from app.modules.validation.schemas.response import (
    ValidationResultResponse,
    ValidationSummary,
)
from app.modules.validation.validators import (
    CitationValidator,
    DOIFormatValidator,
    DuplicateDOIValidator,
    DuplicateTitleValidator,
    DuplicateURLValidator,
    MetadataValidator,
    PublicationValidator,
    URLFormatValidator,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)

# Score deductions for warning-level issues
_SCORE_PENALTIES: dict[str, int] = {
    "missing_abstract": 10,
    "missing_venue": 5,
    "missing_authors": 10,
    "invalid_year": 5,
    "invalid_citation_count": 5,
    "invalid_doi_format": 5,
    "invalid_url": 5,
}

# Rules whose presence forces the status to INVALID regardless of score
_CRITICAL_RULES: set[str] = {
    "duplicate_doi",
    "duplicate_title",
    "duplicate_url",
    "empty_title",
    "future_year",
}


class ValidationService:
    """Orchestrates all validation rules and computes per-paper scores."""

    def __init__(self) -> None:
        self._validators = [
            DuplicateDOIValidator(),
            DuplicateTitleValidator(),
            DuplicateURLValidator(),
            MetadataValidator(),
            PublicationValidator(),
            CitationValidator(),
            DOIFormatValidator(),
            URLFormatValidator(),
        ]

    def validate_papers(
        self,
        papers: list[Paper],
    ) -> ValidationResultResponse:
        """Run every validator against each paper and return results."""
        all_papers = papers
        validated: list[ValidatedPaper] = []
        duplicate_count = 0

        for paper in all_papers:
            issues: list[ValidationIssue] = []
            for validator in self._validators:
                issues.extend(validator.validate(paper, all_papers))

            score, status = self._compute_score_and_status(issues)

            has_critical = any(i.rule in _CRITICAL_RULES for i in issues)
            if has_critical or status == ValidationStatus.INVALID:
                if has_critical:
                    status = ValidationStatus.INVALID
                    score = min(score, 0)

            if any(i.rule.startswith("duplicate_") for i in issues):
                duplicate_count += 1

            validated.append(
                ValidatedPaper(
                    paper=paper.model_dump(),
                    validation_status=status,
                    validation_messages=[i.message for i in issues],
                    validation_score=max(score, 0),
                    validation_timestamp=datetime.now(timezone.utc).isoformat(),
                ),
            )

        valid_count = sum(1 for v in validated if v.validation_status == ValidationStatus.VALID)
        warning_count = sum(1 for v in validated if v.validation_status == ValidationStatus.WARNING)
        invalid_count = sum(1 for v in validated if v.validation_status == ValidationStatus.INVALID)
        avg_score = (
            sum(v.validation_score for v in validated) / len(validated)
            if validated
            else 0.0
        )

        summary = ValidationSummary(
            total_papers=len(validated),
            valid=valid_count,
            warning=warning_count,
            invalid=invalid_count,
            duplicates=duplicate_count,
            average_score=round(avg_score, 1),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "validation_completed",
            total=summary.total_papers,
            valid=summary.valid,
            warning=summary.warning,
            invalid=summary.invalid,
            duplicates=summary.duplicates,
            avg_score=summary.average_score,
        )

        return ValidationResultResponse(
            summary=summary,
            validated_papers=[v.model_dump() for v in validated],
        )

    def _compute_score_and_status(
        self,
        issues: list[ValidationIssue],
    ) -> tuple[int, ValidationStatus]:
        """Calculate score and derive status from non-critical issues only."""
        score = 100
        for issue in issues:
            penalty = _SCORE_PENALTIES.get(issue.rule, 0)
            score -= penalty
        score = max(score, 0)

        if score >= 90:
            status = ValidationStatus.VALID
        elif score >= 70:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.INVALID

        return score, status
