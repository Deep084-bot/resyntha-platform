"""Duplicate URL validator — flags papers whose URL already appears
elsewhere in the result set."""

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class DuplicateURLValidator(BaseValidator):
    """Mark as INVALID when another paper in the same batch has the same URL."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if not paper.url:
            return []
        url_lower = paper.url.lower().strip()
        count = sum(
            1 for p in all_papers
            if p.url and p.url.lower().strip() == url_lower
        )
        if count > 1:
            return [
                ValidationIssue(
                    rule="duplicate_url",
                    message=f"Duplicate URL: {paper.url[:80]}",
                    severity="error",
                ),
            ]
        return []
