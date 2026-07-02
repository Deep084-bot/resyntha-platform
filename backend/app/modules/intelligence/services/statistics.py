"""Basic statistics service.

Frequency distributions, percentiles, z-scores, and other
descriptive statistics used by multiple analyzers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.modules.intelligence.graph.models import ResearchGraph


class StatisticsService:
    """Descriptive statistics for ResearchGraph entities.

    Parameters
    ----------
    graph:
        The research graph to operate on.
    """

    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def frequency_distribution(
        self,
        entity_type: str,
        normalize: bool = True,
    ) -> dict[str, int]:
        """Entity frequency distribution across the corpus.

        Parameters
        ----------
        entity_type:
            ``"author"``, ``"institution"``, ``"methodology"``,
            ``"dataset"``, ``"technology"``, or ``"metric"``.
        normalize:
            If True, lowercase/strip keys.

        Returns
        -------
        ``{entity_name: paper_count}``.
        """
        raise NotImplementedError

    def top_n(self, entity_type: str, n: int = 10) -> list[tuple[str, int]]:
        """Top-*n* most frequent entities of a type."""
        raise NotImplementedError

    def z_scores(self, values: Sequence[float]) -> list[float]:
        """Z-scores for a list of values."""
        raise NotImplementedError

    def percentile(self, values: Sequence[float], p: float) -> float:
        """The *p*-th percentile (0-100) of *values*."""
        raise NotImplementedError
