"""Rule-based gap detection engine.

Each rule extends ``BaseGapRule`` and implements ``evaluate()``,
which receives all ``ExtractedKnowledge`` records and returns a
list of detected ``Gap`` objects. Rules are independent and can
be added without modifying existing ones.
"""

from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext
from app.modules.gap_detection.rules.dataset_gap import DatasetGapRule
from app.modules.gap_detection.rules.evaluation_gap import EvaluationGapRule
from app.modules.gap_detection.rules.future_work_gap import FutureWorkGapRule
from app.modules.gap_detection.rules.limitation_gap import LimitationGapRule
from app.modules.gap_detection.rules.method_combination import MethodCombinationGapRule
from app.modules.gap_detection.rules.temporal_gap import TemporalGapRule

__all__ = [
    "BaseGapRule",
    "DatasetGapRule",
    "EvaluationGapRule",
    "FutureWorkGapRule",
    "LimitationGapRule",
    "MethodCombinationGapRule",
    "RuleContext",
    "TemporalGapRule",
]
