"""Citation grouper — organises citations by claim for structured output."""

from __future__ import annotations

from collections import defaultdict

from app.modules.copilot.evidence.models import EvidenceBundle, GroupedCitation, SupportingPaper


class CitationGrouper:
    """Groups citations by the claims they support.

    Input: EvidenceBundle with items, each referencing supporting papers.
    Output: list of GroupedCitation objects, each with a claim and its papers.
    """

    def group(self, bundle: EvidenceBundle) -> list[GroupedCitation]:
        if not bundle.items:
            return []

        claim_map: dict[str, set[str]] = defaultdict(set)
        paper_map: dict[str, SupportingPaper] = {}

        for item in bundle.items:
            for paper in item.supporting_papers:
                claim_map[item.claim].add(paper.title)
                if paper.title not in paper_map:
                    paper_map[paper.title] = paper

        grouped: list[GroupedCitation] = []
        for claim, titles in claim_map.items():
            papers = [paper_map[t] for t in titles if t in paper_map]
            if papers:
                grouped.append(GroupedCitation(claim=claim, papers=papers))

        return grouped
