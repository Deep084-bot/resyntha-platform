"""Dataset gap rule.

Detects methodologies that appear frequently but are rarely paired
with a specific dataset or technique in the extracted knowledge.

Logic: For each methodology that appears in >= 3 papers, count how
many distinct techniques/datasets co-occur with it. If the ratio of
co-occurring techniques to methodology frequency is below a threshold,
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


class DatasetGapRule(BaseGapRule):
    """Detect methodologies that lack paired dataset/technique coverage."""

    name = "dataset_gap"

    MIN_METHODOLOGY_FREQ = 3
    MIN_TECHNIQUE_RATIO = 0.5
    MAX_RESULTS = 5

    def evaluate(self, ctx: RuleContext) -> list[Gap]:
        gaps: list[Gap] = []

        methodology_counter: Counter[str] = Counter()
        method_to_techniques: dict[str, set[str]] = {}

        for rec in ctx.records:
            method = (rec.methodology or "").strip().lower()
            if not method:
                continue
            methodology_counter[method] += 1
            if method not in method_to_techniques:
                method_to_techniques[method] = set()
            for t in (rec.relevant_techniques or []):
                method_to_techniques[method].add(t.strip().lower())

        for method, freq in methodology_counter.most_common():
            if freq < self.MIN_METHODOLOGY_FREQ:
                continue
            unique_techniques = method_to_techniques.get(method, set())
            ratio = len(unique_techniques) / freq
            if ratio < self.MIN_TECHNIQUE_RATIO and freq >= self.MIN_METHODOLOGY_FREQ:
                gap = Gap(
                    id=f"dataset-gap-{method[:40]}",
                    title=f"Limited dataset/technique coverage for {method}",
                    description=(
                        f"Methodology '{method}' appears in {freq} papers but "
                        f"only {len(unique_techniques)} distinct techniques "
                        f"or datasets co-occur with it (ratio: {ratio:.1f})."
                    ),
                    category=GapCategory.DATASET,
                    confidence=min(round(freq / 10, 2), 0.95),
                    severity=GapSeverity.HIGH if freq >= 5 else GapSeverity.MEDIUM,
                    evidence=Evidence(
                        description=(
                            f"{freq} papers use '{method}' but it is paired "
                            f"with only {len(unique_techniques)} unique techniques"
                        ),
                        supporting_facts=[
                            f"Methodology frequency: {freq}",
                            f"Unique co-occurring techniques: {len(unique_techniques)}",
                            f"Co-occurrence ratio: {ratio:.1f}",
                        ],
                        statistics={
                            "methodology_frequency": freq,
                            "unique_techniques": len(unique_techniques),
                            "co_occurrence_ratio": round(ratio, 2),
                        },
                    ),
                    recommendation=(
                        f"Evaluate '{method}' on additional datasets or techniques "
                        f"beyond the {len(unique_techniques)} currently observed."
                    ),
                )
                gaps.append(gap)

                if len(gaps) >= self.MAX_RESULTS:
                    break

        return gaps
