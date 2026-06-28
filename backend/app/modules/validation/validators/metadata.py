"""Metadata validator — checks for missing title, abstract, authors,
and venue."""

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class MetadataValidator(BaseValidator):
    """Check for empty title, missing abstract, missing authors, missing venue."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not paper.title or not paper.title.strip():
            issues.append(
                ValidationIssue(
                    rule="empty_title",
                    message="Empty title",
                    severity="error",
                ),
            )

        if not paper.abstract:
            issues.append(
                ValidationIssue(
                    rule="missing_abstract",
                    message="Missing abstract",
                    severity="warning",
                ),
            )

        if not paper.authors:
            issues.append(
                ValidationIssue(
                    rule="missing_authors",
                    message="Missing authors",
                    severity="warning",
                ),
            )

        if not paper.venue:
            issues.append(
                ValidationIssue(
                    rule="missing_venue",
                    message="Missing venue",
                    severity="warning",
                ),
            )

        return issues
