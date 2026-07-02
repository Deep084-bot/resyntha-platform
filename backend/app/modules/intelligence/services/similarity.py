"""Similarity / distance service.

Computes paper-to-paper and entity-to-entity similarity for
novelty detection and clustering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.intelligence.graph.models import ResearchGraph


class SimilarityService:
    """Multi-dimensional similarity over the ResearchGraph.

    Parameters
    ----------
    graph:
        The research graph to operate on.
    """

    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def paper_distance(self, paper_a: str, paper_b: str) -> float:
        """Distance between two papers in methodology-technique space.

        Lower values mean more similar.  0 = identical profile.
        """
        raise NotImplementedError

    def most_similar(
        self,
        paper_id: str,
        n: int = 10,
    ) -> list[tuple[str, float]]:
        """Top-*n* papers most similar to *paper_id*.

        Returns ``[(paper_id, distance)]`` sorted by distance ascending.
        """
        raise NotImplementedError

    def outlier_scores(self) -> dict[str, float]:
        """Outlier score for every paper.

        Higher = more unusual relative to the corpus.
        """
        raise NotImplementedError
