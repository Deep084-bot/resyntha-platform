"""Temporal trend analysis service.

Computes year-over-year growth, decline, acceleration, and
emerging/declining classification for any entity type.
Used by the temporal, technology, and methodology analyzers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.intelligence.graph.models import ResearchGraph


class TrendService:
    """Temporal trend analysis over the ResearchGraph.

    Parameters
    ----------
    graph:
        The research graph to operate on.
    """

    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def year_over_year(
        self,
        entity_type: str,
        name: str,
    ) -> dict[int, int]:
        """Paper count per year for a single entity.

        Returns
        -------
        ``{year: paper_count}``.
        """
        raise NotImplementedError

    def growth_rate(self, entity_type: str, name: str) -> float:
        """Compound annual growth rate (CAGR) over available years."""
        raise NotImplementedError

    def is_emerging(self, entity_type: str, name: str, recent_years: int = 3) -> bool:
        """True if the entity appeared only in the last *recent_years*."""
        raise NotImplementedError

    def is_declining(self, entity_type: str, name: str, recent_years: int = 3) -> bool:
        """True if the entity peaked before *recent_years* and has since declined."""
        raise NotImplementedError

    def top_emerging(
        self,
        entity_type: str,
        n: int = 10,
        recent_years: int = 3,
    ) -> list[tuple[str, float]]:
        """Top *n* emerging entities ranked by growth rate."""
        raise NotImplementedError
