"""Evaluation gap rule.

Detects research tasks that are evaluated using only a single metric
across nearly all papers, suggesting a need for more diverse evaluation.

Since our current schema does not explicitly store evaluation metrics,
this rule approximates by checking whether key findings or limitations
mention metric-related terms and whether methodology diversity is low.

Logic: For each methodology present in >= 3 papers, check the
diversity of key findings and limitations for evaluation-related
terms. If evaluation language is uniform (single metric frame),
flag a gap.
"""

import re

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
)
from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext

_METRIC_TERMS = re.compile(
    r"\b(accuracy|precision|recall|f1|bleu|rouge|perplexity|"
    r"mae|rmse|mse|auc|map|ndcg|latency|throughput|"
    r"error\s*rate|f\-?score|metric|evaluation)\b",
    re.IGNORECASE,
)


class EvaluationGapRule(BaseGapRule):
    """Detect methodology areas with narrow evaluation diversity."""

    name = "evaluation_gap"

    MIN_METHOD_FREQ = 3
    SINGLE_METRIC_RATIO = 0.8
    MAX_RESULTS = 3

    def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        method_findings: dict[str, list[str]] = {}

        for rec in ctx.records:
            method = (rec.methodology or "").strip().lower()
            if not method:
                continue
            if method not in method_findings:
                method_findings[method] = []
            for finding in (rec.key_findings or []):
                method_findings[method].append(finding)
            for lim in (rec.limitations or []):
                method_findings[method].append(lim)

        for method, texts in method_findings.items():
            if len(texts) < self.MIN_METHOD_FREQ * 2:
                continue

            metric_mentions = [
                t for t in texts if _METRIC_TERMS.search(t)
            ]

            if not metric_mentions:
                continue

            unique_metrics = len(set(
                m.group(0).lower() for t in metric_mentions
                for m in _METRIC_TERMS.finditer(t)
            ))

            ratio = len(metric_mentions) / len(texts)
            if unique_metrics <= 2 and ratio >= self.SINGLE_METRIC_RATIO:
                gap = Gap(
                    id=f"eval-gap-{method[:40]}",
                    title=f"Limited evaluation diversity for {method}",
                    description=(
                        f"{int(ratio * 100)}% of papers using '{method}' "
                        f"reference only {unique_metrics} distinct evaluation "
                        f"metric(s); a single-metric evaluation standard may "
                        f"hide methodological trade-offs."
                    ),
                    category=GapCategory.EVALUATION,
                    confidence=min(round(ratio, 2), 0.85),
                    severity=GapSeverity.MEDIUM if unique_metrics == 1 else GapSeverity.LOW,
                    evidence=Evidence(
                        description=(
                            f"Papers using '{method}' rely on {unique_metrics} "
                            f"metric(s) in {int(ratio * 100)}% of evaluation descriptions"
                        ),
                        supporting_facts=[
                            f"Evaluation mentions: {len(metric_mentions)}/{len(texts)}",
                            f"Unique metrics found: {unique_metrics}",
                            f"Metric coverage ratio: {ratio:.0%}",
                        ],
                        statistics={
                            "metric_mention_count": len(metric_mentions),
                            "unique_metrics": unique_metrics,
                            "coverage_ratio": round(ratio, 2),
                        },
                    ),
                    recommendation=(
                        f"Explore additional evaluation metrics for '{method}' "
                        f"— currently dominated by {unique_metrics} metric(s). "
                        f"Broader evaluation may reveal new insights."
                    ),
                )
                gaps.append(gap)

                if len(gaps) >= self.MAX_RESULTS:
                    break

        return gaps
