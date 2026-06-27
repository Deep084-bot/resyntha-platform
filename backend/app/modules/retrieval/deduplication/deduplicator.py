"""Deduplicator — removes duplicate papers from a merged result set.

Deduplication strategy (in order of precedence):
1.  DOI match
2.  Exact title match (case-insensitive)
3.  Normalised title match (lowercased, stripped, punctuation removed)
"""

import re
from collections.abc import Sequence

from app.modules.retrieval.domain.paper import Paper


def deduplicate(papers: Sequence[Paper]) -> list[Paper]:
    """Return a list with duplicates removed, preserving the first occurrence.

    The deduplication chain checks DOI first, then exact title, then
    normalised title.
    """
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    seen_normalized: set[str] = set()
    unique: list[Paper] = []

    for paper in papers:
        if _is_duplicate(paper, seen_dois, seen_titles, seen_normalized):
            continue

        if paper.doi:
            seen_dois.add(paper.doi.lower())
        seen_titles.add(paper.title.lower().strip())
        seen_normalized.add(_normalize_title(paper.title))
        unique.append(paper)

    return unique


def _is_duplicate(
    paper: Paper,
    seen_dois: set[str],
    seen_titles: set[str],
    seen_normalized: set[str],
) -> bool:
    if paper.doi and paper.doi.lower() in seen_dois:
        return True
    title_key = paper.title.lower().strip()
    if title_key in seen_titles:
        return True
    if _normalize_title(paper.title) in seen_normalized:
        return True
    return False


def _normalize_title(title: str) -> str:
    """Lowercase, strip whitespace, and remove common punctuation."""
    normalized = title.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
