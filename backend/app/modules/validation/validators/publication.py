"""Publication validator — checks for invalid or future publication years."""

from datetime import datetime, timezone

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class PublicationValidator(BaseValidator):
    """Check year validity: past future years are INVALID, very old
    years are downgraded."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if paper.year is None:
            return issues

        current_year = datetime.now(timezone.utc).year

        if paper.year > current_year:
            issues.append(
                ValidationIssue(
                    rule="future_year",
                    message=f"Publication year {paper.year} is in the future",
                    severity="error",
                ),
            )
        elif paper.year < 1900:
            issues.append(
                ValidationIssue(
                    rule="invalid_year",
                    message=f"Publication year {paper.year} is before 1900",
                    severity="warning",
                ),
            )

        return issues
