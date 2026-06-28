"""URL format validator — checks that URLs are well-formed."""

from urllib.parse import urlparse

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue
from app.modules.validation.validators.base import BaseValidator


class URLFormatValidator(BaseValidator):
    """Flag URLs that are not valid absolute URLs."""

    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        if not paper.url:
            return []
        try:
            parsed = urlparse(paper.url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Missing scheme or netloc")
        except Exception:
            return [
                ValidationIssue(
                    rule="invalid_url",
                    message=f"Invalid URL: {paper.url[:80]}",
                    severity="warning",
                ),
            ]
        return []
