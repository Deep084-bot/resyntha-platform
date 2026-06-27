"""Normaliser — converts provider-specific responses into ``Paper``.

Each provider returns data in a different shape; the normaliser maps
those shapes onto the single ``Paper`` model so the rest of the
pipeline only ever deals with one type.
"""

from app.modules.retrieval.domain.paper import Paper


def normalize_semantic_scholar(raw: dict) -> Paper:
    """Convert a Semantic Scholar response dict to a canonical ``Paper``."""
    authors = []
    for a in raw.get("authors") or []:
        if isinstance(a, dict) and "name" in a:
            authors.append(a["name"])

    external_ids = raw.get("externalIds") or {}

    doi = external_ids.get("DOI")
    if not doi:
        doi = _extract_doi_from_url(raw.get("url", ""))

    return Paper(
        title=raw.get("title", "").strip(),
        abstract=raw.get("abstract"),
        authors=authors,
        year=raw.get("year"),
        venue=raw.get("venue"),
        doi=doi,
        url=raw.get("url"),
        citation_count=raw.get("citationCount"),
        source="semantic_scholar",
    )


def normalize_arxiv(raw: dict) -> Paper:
    """Convert an arXiv response dict to a canonical ``Paper``."""
    doi = raw.get("doi")
    year = None
    published = raw.get("published")
    if published is not None:
        year = published.year

    return Paper(
        title=raw.get("title", "").strip(),
        abstract=raw.get("summary"),
        authors=raw.get("authors", []),
        year=year,
        doi=doi,
        url=raw.get("link"),
        source="arxiv",
    )


def _extract_doi_from_url(url: str) -> str | None:
    """Extract a DOI from a URL like https://doi.org/10.1234/..."""
    if not url:
        return None
    if "/doi.org/" in url:
        return url.split("/doi.org/", 1)[-1]
    return None
