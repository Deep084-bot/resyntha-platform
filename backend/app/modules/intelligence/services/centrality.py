"""Centrality analysis service.

Measures node importance in entity graphs (co-authorship,
institution collaboration).  Used by the collaboration
and institution analyzers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.intelligence.graph.models import ResearchGraph


class CentralityService:
    """Centrality / importance measures over the ResearchGraph.

    Parameters
    ----------
    graph:
        The research graph to operate on.
    """

    def __init__(self, graph: ResearchGraph) -> None:
        self._graph = graph

    def degree_centrality(self, entity_type: str) -> dict[str, float]:
        """Normalised degree centrality for all entities of a type.

        Parameters
        ----------
        entity_type:
            ``"author"`` or ``"institution"``.

        Returns
        -------
        ``{name: centrality}`` where centrality is in [0, 1].
        """
        raise NotImplementedError

    def co_authorship_edges(self) -> list[tuple[str, str, int]]:
        """Co-authorship edges ``(author_a, author_b, weight)``.

        Weight = number of papers the two authors share.
        """
        raise NotImplementedError

    def collaboration_edges(
        self,
    ) -> list[tuple[str, str, int]]:
        """Institution collaboration edges ``(inst_a, inst_b, weight)``.

        Weight = number of papers the two institutions share.
        """
        raise NotImplementedError
