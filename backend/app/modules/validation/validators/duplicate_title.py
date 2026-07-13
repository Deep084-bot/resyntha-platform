"""Duplicate title validator — flags papers whose title (case-insensitive)
already appears elsewhere in the result set."""

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class DuplicateTitleValidator(BaseValidator):
    """Mark as INVALID when another paper in the same batch has the same title."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if not paper.title:
            return []
        title_lower = paper.title.lower().strip()
        count = sum(1 for p in all_papers if p.title and p.title.lower().strip() == title_lower)
        if count > 1:
            return [
                ValidationIssue(
                    rule="duplicate_title",
                    message=f"Duplicate title: {paper.title[:80]}",
                    severity="error",
                ),
            ]
        return []
