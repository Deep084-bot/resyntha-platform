"""Co-occurrence analysis service.

Computes how often pairs of entities appear together across the
corpus (e.g., methodology X with dataset Y, or author A with
author B).  Used by methodology, dataset, and novelty analyzers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.modules.intelligence.graph.models import ResearchGraph


class CoOccurrenceService:
    """Co-occurrence computation for ResearchGraph entities.

    Parameters
    ----------
    graph:
        The research graph to operate on.
    """

    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def between(
        self,
        entity_a_type: str,
        name_a: str,
        entity_b_type: str,
        name_b: str,
    ) -> int:
        """Count papers where both entities appear together.

        Parameters
        ----------
        entity_a_type:
            One of ``"author"``, ``"institution"``, ``"methodology"``,
            ``"dataset"``, ``"technology"``, ``"metric"``.
        name_a:
            Canonical name of the first entity.
        entity_b_type, name_b:
            Second entity.

        Returns
        -------
        Number of papers containing both entities.
        """
        raise NotImplementedError

    def matrix(
        self,
        entity_type: str,
        names: Sequence[str] | None = None,
    ) -> dict[str, dict[str, int]]:
        """Pairwise co-occurrence matrix for entities of *entity_type*.

        Parameters
        ----------
        entity_type:
            Entity type to compute the matrix for.
        names:
            Subset of entities to include.  ``None`` means all.

        Returns
        -------
        ``{entity_a: {entity_b: count}}``  (symmetric, diagonal = 0).
        """
        raise NotImplementedError

    def top_co_occurring(
        self,
        entity_type: str,
        name: str,
        n: int = 10,
    ) -> list[tuple[str, int]]:
        """Top-*n* entities that co-occur most with *name*."""
        raise NotImplementedError
