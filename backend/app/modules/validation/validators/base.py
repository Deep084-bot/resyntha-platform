"""Base validator — all rule validators inherit from this."""

from abc import ABC, abstractmethod

from app.modules.retrieval.domain.paper import Paper
from app.modules.validation.domain.validated_paper import ValidationIssue


class BaseValidator(ABC):
    """Abstract base for a single validation rule.

    Subclasses implement ``validate()`` which inspects one paper
    (and optionally the full result set for deduplication) and
    returns zero or more ``ValidationIssue`` objects.
    """

    @abstractmethod
    def validate(
        self,
        paper: Paper,
        all_papers: list[Paper],
    ) -> list[ValidationIssue]:
        """Run this rule against *paper* in the context of *all_papers*.

        Returns an empty list when no issues are found.
        """
