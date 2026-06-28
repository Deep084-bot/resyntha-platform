"""DOI format validator — checks that DOIs match a valid pattern."""

import re

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator

_DOI_PATTERN = re.compile(r"^10\.\d{4,}/[\w.\-;()/:<>]+$")


class DOIFormatValidator(BaseValidator):
    """Flag DOIs that do not match the standard DOI syntax."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if not paper.doi:
            return []
        if not _DOI_PATTERN.match(paper.doi.strip()):
            return [
                ValidationIssue(
                    rule="invalid_doi_format",
                    message=f"Invalid DOI format: {paper.doi}",
                    severity="warning",
                ),
            ]
        return []
