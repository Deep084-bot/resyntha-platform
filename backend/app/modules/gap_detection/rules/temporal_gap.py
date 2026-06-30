"""Temporal gap rule.

Detects research topics or techniques that appeared in early papers
but disappeared from recent publications, suggesting a revival
opportunity.

Logic: Group papers by year. For each technique or methodology,
track its presence across years. If it appeared in >= 2 papers in
early years but 0 papers in the most recent year range, flag a gap.
"""

from collections import defaultdict

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
)
from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext


class TemporalGapRule(BaseGapRule):
    """Detect topics that have disappeared from recent publications."""

    name = "temporal_gap"

    MIN_EARLY_APPEARANCES = 2
    RECENT_YEARS = 2
    MAX_RESULTS = 5

    def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        technique_years: dict[str, set[str]] = defaultdict(set)
        methodology_years: dict[str, set[str]] = defaultdict(set)
        technique_papers: dict[str, list[str]] = defaultdict(list)
        methodology_papers: dict[str, list[str]] = defaultdict(list)

        all_years: set[str] = set()

        for rec in ctx.records:
            year = getattr(rec, "created_at", None)
            year_str = str(year.year) if hasattr(year, "year") else ""

            if not year_str:
                continue
            all_years.add(year_str)

            for tech in (rec.relevant_techniques or []):
                key = tech.strip().lower()
                if key:
                    technique_years[key].add(year_str)
                    technique_papers[key].append(rec.paper_title)

            method = (rec.methodology or "").strip().lower()
            if method:
                methodology_years[method].add(year_str)
                methodology_papers[method].append(rec.paper_title)

        if len(all_years) < 3:
            return gaps

        sorted_years = sorted(all_years)
        recent_cutoff = (
            sorted_years[-self.RECENT_YEARS]
            if len(sorted_years) >= self.RECENT_YEARS
            else sorted_years[-1]
        )
        recent_set = (
            set(sorted_years[-self.RECENT_YEARS:])
            if len(sorted_years) >= self.RECENT_YEARS
            else {sorted_years[-1]}
        )
        early_years = [y for y in sorted_years if y < recent_cutoff]

        candidates: list[tuple[str, int, set[str], list[str], str]] = []

        for term, years in technique_years.items():
            early_count = sum(1 for y in years if y in early_years)
            recent_count = sum(1 for y in years if y in recent_set)
            if early_count >= self.MIN_EARLY_APPEARANCES and recent_count == 0:
                candidates.append((
                    term, early_count, years, technique_papers[term], "technique"
                ))

        for term, years in methodology_years.items():
            early_count = sum(1 for y in years if y in early_years)
            recent_count = sum(1 for y in years if y in recent_set)
            if early_count >= self.MIN_EARLY_APPEARANCES and recent_count == 0:
                candidates.append((
                    term, early_count, years, methodology_papers[term], "methodology"
                ))

        candidates.sort(key=lambda x: x[1], reverse=True)

        for term, early_count, years, papers, kind in candidates[:self.MAX_RESULTS]:
            year_range = f"{min(years)}–{max(years)}" if len(years) > 1 else list(years)[0]
            gap = Gap(
                id=f"temporal-gap-{term[:40]}",
                title=f"Dormant {kind}: {term[:80]}",
                description=(
                    f"'{term}' ({kind}) appeared in {early_count} papers "
                    f"during {year_range} but has zero publications in the "
                    f"most recent {self.RECENT_YEARS} year(s) of this corpus."
                ),
                category=GapCategory.TEMPORAL,
                confidence=min(round(early_count / 5, 2), 0.85),
                severity=GapSeverity.MEDIUM if early_count >= 4 else GapSeverity.LOW,
                evidence=Evidence(
                    description=(
                        f"Active in {year_range} ({early_count} papers), "
                        f"absent from recent publications"
                    ),
                    supporting_paper_ids=papers[:5],
                    supporting_facts=[
                        f"Active years: {year_range}",
                        f"Early paper count: {early_count}",
                        "Recent paper count: 0",
                        f"Category: {kind}",
                    ],
                    statistics={
                        "early_paper_count": early_count,
                        "recent_paper_count": 0,
                        "active_year_range": year_range,
                    },
                ),
                recommendation=(
                    f"Consider revisiting '{term}' — it generated "
                    f"{early_count} papers in {year_range} but has no "
                    f"recent activity in this corpus, suggesting a "
                    f"potential revival opportunity."
                ),
            )
            gaps.append(gap)

        return gaps
