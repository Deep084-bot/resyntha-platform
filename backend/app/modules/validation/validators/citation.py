"""Citation validator — flags negative citation counts."""

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class CitationValidator(BaseValidator):
    """Flag citation counts below zero."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if paper.citation_count is not None and paper.citation_count < 0:
            return [
                ValidationIssue(
                    rule="invalid_citation_count",
                    message=f"Invalid citation count: {paper.citation_count}",
                    severity="warning",
                ),
            ]
        return []
