"""Gap detection service — orchestrates rule-based research gap analysis.

``GapDetectionService`` is stateless per run. It:

1. Fetches all ``ExtractedKnowledge`` records for an investigation.
2. Runs each registered rule against the data.
3. Aggregates results into a ``ResearchGapReport``.
4. Creates a ``RESEARCH_GAP_REPORT`` artifact.

No LLM calls — everything is deterministic rule matching.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.gap_detection.artifact.builder import GapArtifactBuilder
from app.modules.gap_detection.domain.gap import (
    Gap,
    GapSummary,
    ResearchGapReport,
)
from app.modules.gap_detection.rules import (
    BaseGapRule,
    DatasetGapRule,
    EvaluationGapRule,
    FutureWorkGapRule,
    LimitationGapRule,
    MethodCombinationGapRule,
    RuleContext,
    TemporalGapRule,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_RULES: list[type[BaseGapRule]] = [
    DatasetGapRule,
    FutureWorkGapRule,
    LimitationGapRule,
    MethodCombinationGapRule,
    EvaluationGapRule,
    TemporalGapRule,
]


class GapDetectionService:
    """Orchestrate rule-based gap detection for an investigation.

    Parameters
    ----------
    session:
        Async SQLAlchemy session.
    rules:
        List of rule classes to run. Defaults to all built-in rules.
    """

    def __init__(
        self,
        session: Session,
        rules: list[type[BaseGapRule]] | None = None,
    ) -> None:
        self._session = session
        self._extraction_repo = ExtractionRepository(session)
        self._artifact_builder = GapArtifactBuilder(session)
        self._rule_classes = rules or _DEFAULT_RULES

    def detect_gaps(
        self,
        investigation_id: uuid.UUID,
        execution_id: uuid.UUID | None = None,
    ) -> ResearchGapReport:
        """Run all gap detection rules and create a report artifact.

        Returns the computed ``ResearchGapReport``.
        """
        records = self._extraction_repo.list_by_investigation(
            investigation_id,
        )

        ctx = RuleContext(records)

        all_gaps: list[Gap] = []
        triggered_rules = 0
        for rule_cls in self._rule_classes:
            rule = rule_cls()
            try:
                gaps = rule.evaluate(ctx)
                if gaps:
                    triggered_rules += 1
                    all_gaps.extend(gaps)
            except Exception:
                logger.exception(
                    "gap_rule_failed",
                    rule=rule.name,
                    investigation_id=str(investigation_id),
                )

        report = self._build_report(all_gaps)

        self._artifact_builder.create_gap_report_artifact(
            investigation_id=investigation_id,
            report=report,
            execution_id=execution_id,
        )

        self._session.commit()

        logger.info(
            "gap_detection_complete",
            investigation_id=str(investigation_id),
            total_gaps=report.summary.total_gaps,
            rules_triggered=triggered_rules,
        )

        return report

    def _build_report(self, gaps: list[Gap]) -> ResearchGapReport:
        """Aggregate detected gaps into a structured report."""
        categories: dict[str, int] = {}
        severities: dict[str, int] = {}
        high_confidence = 0

        for gap in gaps:
            cat = gap.category.value
            categories[cat] = categories.get(cat, 0) + 1

            sev = gap.severity.value
            severities[sev] = severities.get(sev, 0) + 1

            if gap.confidence >= 0.7:
                high_confidence += 1

        recommendations = [
            g.recommendation for g in gaps if g.recommendation
        ]

        return ResearchGapReport(
            summary=GapSummary(
                total_gaps=len(gaps),
                high_confidence_gaps=high_confidence,
                categories=categories,
                severities=severities,
            ),
            gaps=gaps,
            statistics={
                "total_gaps": len(gaps),
                "high_confidence_gaps": high_confidence,
                "categories_detected": len(categories),
                "rules_triggered": len([g for g in gaps if g]),
            },
            recommendations=recommendations,
            generated_at=datetime.now(UTC).isoformat(),
        )
