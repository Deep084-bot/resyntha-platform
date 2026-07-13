"""Scorer — assigns a composite relevance score to each paper.

Composite score formula:
  50 %  semantic relevance   (placeholder — always 0.5 for now)
  30 %  citation count       (normalised log scale)
  20 %  recency              (normalised to [0, 1] based on current year)
"""

import math
from collections.abc import Sequence
from datetime import date

from app.modules.retrieval.domain.paper import Paper


def rank(papers: Sequence[Paper]) -> list[Paper]:
    """Return papers sorted by composite score descending.

    Each paper's ``score`` field is set to its computed value.
    """
    current_year = date.today().year
    max_citations = _max_citation_count(papers)

    scored: list[tuple[float, Paper]] = []
    for paper in papers:
        s = _compute_score(paper, current_year, max_citations)
        scored.append((s, paper.model_copy(update={"score": s})))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [paper for _, paper in scored]


def _compute_score(paper: Paper, current_year: int, max_citations: int) -> float:
    semantic_score = 0.5  # placeholder; will be replaced by LLM later
    citation_score = _citation_score(paper.citation_count, max_citations)
    recency_score = _recency_score(paper.year, current_year)

    return semantic_score * 0.50 + citation_score * 0.30 + recency_score * 0.20


def _citation_score(citation_count: int | None, max_citations: int) -> float:
    if not citation_count or max_citations <= 0:
        return 0.0
    return min(math.log1p(citation_count) / math.log1p(max_citations), 1.0)


def _recency_score(year: int | None, current_year: int) -> float:
    if not year:
        return 0.0
    age = current_year - year
    if age <= 0:
        return 1.0
    return max(1.0 / (1.0 + math.log1p(age)), 0.0)


def _max_citation_count(papers: Sequence[Paper]) -> int:
    return max((p.citation_count or 0) for p in papers)
