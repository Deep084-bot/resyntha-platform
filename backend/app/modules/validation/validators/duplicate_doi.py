"""Duplicate DOI validator — flags papers whose DOI already appears
elsewhere in the result set."""

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class DuplicateDOIValidator(BaseValidator):
    """Mark as INVALID when another paper in the same batch has the same DOI."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if not paper.doi:
            return []
        count = sum(1 for p in all_papers if p.doi and p.doi.lower() == paper.doi.lower())
        if count > 1:
            return [
                ValidationIssue(
                    rule="duplicate_doi",
                    message=f"Duplicate DOI: {paper.doi}",
                    severity="error",
                ),
            ]
        return []
