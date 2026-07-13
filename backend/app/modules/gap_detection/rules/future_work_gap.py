"""Future work gap rule.

Detects future research directions that are frequently recommended
across papers but never appear as implemented work in any paper's
key findings, contributions, or methodology.

Logic: Count how many papers recommend a future work direction.
For each direction mentioned in >= 3 papers, check whether it
also appears in any paper's key findings or contributions. If
not, it is an underexplored opportunity.
"""

from collections import Counter

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
)
from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext


class FutureWorkGapRule(BaseGapRule):
    """Detect frequently recommended but unimplemented future work."""

    name = "future_work_gap"

    MIN_MENTIONS = 3
    MAX_RESULTS = 5

    def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        fw_counter: Counter[str] = Counter()
        all_findings: set[str] = set()
        all_contributions: set[str] = set()
        paper_titles: dict[str, list[str]] = {}

        for rec in ctx.records:
            for fw in rec.future_work or []:
                key = fw.strip().lower()
                if key:
                    fw_counter[key] += 1
                    if key not in paper_titles:
                        paper_titles[key] = []
                    paper_titles[key].append(rec.paper_title)
            for finding in rec.key_findings or []:
                all_findings.add(finding.strip().lower())
            for contrib in rec.key_contributions or []:
                all_contributions.add(contrib.strip().lower())

        for fw_direction, count in fw_counter.most_common():
            if count < self.MIN_MENTIONS:
                continue

            implemented_in_findings = any(fw_direction in finding for finding in all_findings)
            implemented_in_contributions = any(
                fw_direction in contrib for contrib in all_contributions
            )

            if not implemented_in_findings and not implemented_in_contributions:
                supporting = paper_titles.get(fw_direction, [])
                gap = Gap(
                    id=f"future-work-gap-{fw_direction[:40]}",
                    title=f"Underexplored: {fw_direction[:80]}",
                    description=(
                        f"'{fw_direction}' is recommended as future work in "
                        f"{count} papers but does not appear in any paper's "
                        f"implemented findings or contributions."
                    ),
                    category=GapCategory.FUTURE_WORK,
                    confidence=min(round(count / 8, 2), 0.95),
                    severity=GapSeverity.HIGH if count >= 5 else GapSeverity.MEDIUM,
                    evidence=Evidence(
                        description=(
                            f"Recommended by {count} papers as future work, "
                            f"zero implementations found"
                        ),
                        supporting_paper_ids=supporting[:5],
                        supporting_facts=[
                            f"Papers recommending: {count}",
                            f"Implemented in findings: {implemented_in_findings}",
                            f"Implemented in contributions: {implemented_in_contributions}",
                        ],
                        statistics={
                            "recommendation_count": count,
                            "implemented_count": 0,
                        },
                    ),
                    recommendation=(
                        f"Explore '{fw_direction}' as a research direction — "
                        f"it is recommended by {count} papers but has no "
                        f"documented implementation in this corpus."
                    ),
                )
                gaps.append(gap)

                if len(gaps) >= self.MAX_RESULTS:
                    break

        return gaps
