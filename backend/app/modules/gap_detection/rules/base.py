"""Abstract base class for gap detection rules.

Every rule is a self-contained unit that analyses extracted knowledge
and returns a list of detected gaps. Rules receive a ``RuleContext``
with all available data and produce ``Gap`` objects.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.modules.extraction.domain.models import ExtractedKnowledge
from app.modules.gap_detection.domain.gap import Gap


class RuleContext:
    """Context passed to every rule during evaluation.

    Attributes
    ----------
    records:
        All ``ExtractedKnowledge`` records for the investigation.
    paper_count:
        Total number of papers analyzed.
    """

    def __init__(
        self,
        records: Sequence[ExtractedKnowledge],
    ) -> None:
        self.records = records
        self.paper_count = len(records)

    def flatten_field(self, field: str) -> list[str]:
        """Collect and flatten a field across all records."""
        result: list[str] = []
        for rec in self.records:
            value = getattr(rec, field, None)
            if value is None:
                continue
            if isinstance(value, list):
                result.extend(str(v) for v in value if v)
            else:
                result.append(str(value))
        return result


class BaseGapRule(ABC):
    """Abstract rule that detects a specific category of research gap.

    Subclasses must set ``name`` and implement ``evaluate()``.
    Rules should be stateless — all state lives in ``RuleContext``.
    """

    name: str = ""

    @abstractmethod
    async def evaluate(self, ctx: RuleContext) -> list[Gap]:
        """Analyse the context and return detected gaps."""
