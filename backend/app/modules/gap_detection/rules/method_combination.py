"""Method combination gap rule.

Detects pairs of methodologies or techniques that are individually
common but rarely co-occur in the same paper, suggesting an
underexplored combination.

Logic: Build a co-occurrence matrix of methodology-technique pairs.
For each pair where both elements appear in >= 3 papers but appear
together in < 2 papers, flag a potential research opportunity.
"""

from collections import Counter, defaultdict

from app.modules.gap_detection.domain.gap import (
    Evidence,
    Gap,
    GapCategory,
    GapSeverity,
)
from app.modules.gap_detection.rules.base import BaseGapRule, RuleContext


class MethodCombinationGapRule(BaseGapRule):
    """Detect individually common but rarely combined methods."""

    name = "method_combination"

    MIN_INDIVIDUAL_FREQ = 3
    MIN_COMBINED_FREQ = 2
    MAX_RESULTS = 5

    def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        technique_counter: Counter[str] = Counter()
        method_counter: Counter[str] = Counter()
        method_tech_pairs: dict[tuple[str, str], int] = defaultdict(int)
        paper_titles_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)

        for rec in ctx.records:
            method = (rec.methodology or "").strip().lower()
            techniques = [t.strip().lower() for t in (rec.relevant_techniques or []) if t.strip()]

            if method:
                method_counter[method] += 1

            for tech in techniques:
                technique_counter[tech] += 1

            if method:
                for tech in techniques:
                    pair = (method, tech)
                    method_tech_pairs[pair] += 1
                    if rec.paper_title:
                        paper_titles_by_pair[pair].add(rec.paper_title)

        top_methods = {
            m for m, c in method_counter.most_common(15) if c >= self.MIN_INDIVIDUAL_FREQ
        }
        top_techniques = {
            t for t, c in technique_counter.most_common(15) if c >= self.MIN_INDIVIDUAL_FREQ
        }

        considered_pairs: set[tuple[str, str]] = set()
        for method in top_methods:
            for technique in top_techniques:
                if method == technique:
                    continue
                pair = (method, technique)
                if pair in considered_pairs:
                    continue
                considered_pairs.add(pair)

                co_occurrences = method_tech_pairs.get(pair, 0)
                if co_occurrences < self.MIN_COMBINED_FREQ:
                    method_freq = method_counter.get(method, 0)
                    tech_freq = technique_counter.get(technique, 0)

                    gap = Gap(
                        id=f"method-combo-{method[:20]}-{technique[:20]}",
                        title=f"Underexplored combination: {method} + {technique}",
                        description=(
                            f"Methodology '{method}' appears in {method_freq} papers "
                            f"and technique '{technique}' appears in {tech_freq} papers, "
                            f"but they co-occur in only {co_occurrences} paper(s)."
                        ),
                        category=GapCategory.METHOD_COMBINATION,
                        confidence=min(round((method_freq + tech_freq) / 20, 2), 0.9),
                        severity=(
                            GapSeverity.HIGH
                            if method_freq >= 5 and tech_freq >= 5
                            else GapSeverity.MEDIUM
                        ),
                        evidence=Evidence(
                            description=(
                                f"'{method}' ({method_freq} papers) and "
                                f"'{technique}' ({tech_freq} papers) co-occur "
                                f"in only {co_occurrences} paper(s)"
                            ),
                            supporting_facts=[
                                f"Methodology frequency: {method_freq}",
                                f"Technique frequency: {tech_freq}",
                                f"Co-occurrence count: {co_occurrences}",
                            ],
                            statistics={
                                "methodology_frequency": method_freq,
                                "technique_frequency": tech_freq,
                                "co_occurrence_count": co_occurrences,
                            },
                        ),
                        recommendation=(
                            f"Combine '{method}' with '{technique}' in a single study "
                            f"— they are individually well-explored but rarely applied together."
                        ),
                    )
                    gaps.append(gap)

                    if len(gaps) >= self.MAX_RESULTS:
                        return gaps

        return gaps
