"""RankingEngine — deterministic paper scoring with configurable weights.

Score components (configurable via the ``weights`` dict):
- ``citation`` (default 0.35) — log-normalised citation count
- ``recency`` (default 0.25) — recency score, newer is better
- ``completeness`` (default 0.20) — metadata richness (abstract, DOI, venue)
- ``provider_confidence`` (default 0.20) — confidence based on provider reliability

All scores are normalised to a 0–100 scale.
"""

import math
from collections.abc import Sequence
from datetime import date

from app.modules.retrieval.domain.paper import Paper

DEFAULT_WEIGHTS = {
    "citation": 0.35,
    "recency": 0.25,
    "completeness": 0.20,
    "provider_confidence": 0.20,
}

PROVIDER_CONFIDENCE: dict[str, float] = {
    "semantic_scholar": 1.0,
    "arxiv": 0.7,
    "openalex": 0.9,
    "crossref": 0.8,
}


class RankingEngine:
    """Deterministic paper ranking with configurable weights."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}

    def __call__(self, papers: Sequence[Paper]) -> list[Paper]:
        return self.rank(papers)

    def rank(self, papers: Sequence[Paper]) -> list[Paper]:
        current_year = date.today().year
        max_citations = self._max_citation_count(papers)

        scored: list[tuple[float, Paper]] = []
        for paper in papers:
            score = self._compute_score(paper, current_year, max_citations)
            scored.append((score, paper.model_copy(update={"score": round(score, 2)})))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [paper for _, paper in scored]

    def _compute_score(self, paper: Paper, current_year: int, max_citations: int) -> float:
        citation = self._citation_score(paper.citation_count, max_citations)
        recency = self._recency_score(paper.year, current_year)
        completeness = self._completeness_score(paper)
        provider_conf = self._provider_confidence(paper.source)

        raw = (
            citation * self._weights["citation"]
            + recency * self._weights["recency"]
            + completeness * self._weights["completeness"]
            + provider_conf * self._weights["provider_confidence"]
        )
        return raw * 100.0

    def _citation_score(self, citation_count: int | None, max_citations: int) -> float:
        if not citation_count or max_citations <= 0:
            return 0.0
        return min(math.log1p(citation_count) / math.log1p(max_citations), 1.0)

    def _recency_score(self, year: int | None, current_year: int) -> float:
        if not year:
            return 0.0
        age = current_year - year
        if age <= 0:
            return 1.0
        return max(1.0 / (1.0 + math.log1p(age)), 0.0)

    def _completeness_score(self, paper: Paper) -> float:
        checks = [
            bool(paper.abstract and len(paper.abstract) > 50),
            bool(paper.doi),
            bool(paper.venue),
            bool(paper.authors),
            bool(paper.url),
        ]
        return sum(checks) / len(checks)

    def _provider_confidence(self, source: str) -> float:
        return PROVIDER_CONFIDENCE.get(source, 0.5)

    @staticmethod
    def _max_citation_count(papers: Sequence[Paper]) -> int:
        return max((p.citation_count or 0) for p in papers)
