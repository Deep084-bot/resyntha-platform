"""Canonical paper model.

After normalisation every provider's response is converted into this
common representation.  The model carries enough metadata for
deduplication, ranking, and display.
"""

from pydantic import BaseModel


class Paper(BaseModel):
    """Normalised, deduplicated paper ready for ranking."""

    title: str
    abstract: str | None = None
    authors: list[str] = []
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    citation_count: int | None = None
    source: str = ""
    score: float = 0.0
    metadata: dict = {}
