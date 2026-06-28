"""Limitation gap rule.

Detects limitations that are frequently acknowledged across papers
but no methodology or technique is documented to address them.

Logic: Collect all limitations. For each limitation mentioned in
>= 3 papers, check whether any paper's methodology, techniques, or
contributions reference a solution. If no paper addresses it,
flag a gap.
"""

from collections import Counter

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
)
from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext


class LimitationGapRule(BaseGapRule):
    """Detect frequently mentioned limitations that lack solutions."""

    name = "limitation_gap"

    MIN_MENTIONS = 3
    MAX_RESULTS = 5

    async def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        limitation_counter: Counter[str] = Counter()
        all_techniques_flat: set[str] = set()
        all_findings_flat: set[str] = set()
        all_methods_flat: set[str] = set()
        paper_titles: dict[str, list[str]] = {}

        for rec in ctx.records:
            method = (rec.methodology or "").strip().lower()
            if method:
                all_methods_flat.add(method)
            for finding in (rec.key_findings or []):
                all_findings_flat.add(finding.strip().lower())
            for tech in (rec.relevant_techniques or []):
                all_techniques_flat.add(tech.strip().lower())
            for lim in (rec.limitations or []):
                key = lim.strip().lower()
                if key:
                    limitation_counter[key] += 1
                    if key not in paper_titles:
                        paper_titles[key] = []
                    paper_titles[key].append(rec.paper_title)

        solution_space = all_methods_flat | all_techniques_flat | all_findings_flat

        for limitation, count in limitation_counter.most_common():
            if count < self.MIN_MENTIONS:
                continue

            addressed = any(
                limitation in solution for solution in solution_space
            )

            if not addressed:
                supporting = paper_titles.get(limitation, [])
                gap = Gap(
                    id=f"limitation-gap-{limitation[:40]}",
                    title=f"Unaddressed limitation: {limitation[:80]}",
                    description=(
                        f"'{limitation}' is acknowledged as a limitation in "
                        f"{count} papers, but no methodology or technique in "
                        f"the corpus addresses it."
                    ),
                    category=GapCategory.LIMITATION,
                    confidence=min(round(count / 8, 2), 0.95),
                    severity=GapSeverity.HIGH if count >= 5 else GapSeverity.MEDIUM,
                    evidence=Evidence(
                        description=(
                            f"Mentioned as limitation by {count} papers, "
                            f"zero solutions found"
                        ),
                        supporting_paper_ids=supporting[:5],
                        supporting_facts=[
                            f"Papers acknowledging: {count}",
                            "Methodologies addressing: 0",
                        ],
                        statistics={
                            "acknowledgement_count": count,
                            "addressed_count": 0,
                        },
                    ),
                    recommendation=(
                        f"Explore solutions that address '{limitation}' — "
                        f"it is acknowledged by {count} papers but no existing "
                        f"work in this corpus resolves it."
                    ),
                )
                gaps.append(gap)

                if len(gaps) >= self.MAX_RESULTS:
                    break

        return gaps
