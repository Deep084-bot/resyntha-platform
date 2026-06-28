"""Deterministic clustering for research terms.

Groups similar terms using normalized forms, then ranks by frequency.
No ML, no embeddings — purely lexical normalization + frequency.
"""

from collections import Counter

from app.modules.analysis.cluster.normalizer import Normalizer
from app.modules.analysis.domain.landscape import RankedItem


class Clusterer:
    """Clusters and ranks terms from a list of raw strings.

    Usage::

        clusterer = Clusterer()
        ranked = clusterer.cluster_and_rank(["deep learning", "Deep Learning", "Neural Nets"])
        # → [RankedItem(name="deep learning", count=2, pct=66.7),
        #     RankedItem(name="neural nets", count=1, pct=33.3)]
    """

    def __init__(self, normalizer: Normalizer | None = None) -> None:
        self._normalizer = normalizer or Normalizer()

    def cluster_and_rank(
        self,
        terms: list[str],
        min_count: int = 1,
        max_results: int = 20,
    ) -> list[RankedItem]:
        """Normalize, deduplicate, count, and rank terms.

        Parameters
        ----------
        terms:
            Raw term strings to cluster.
        min_count:
            Minimum frequency to include in results.
        max_results:
            Maximum number of ranked items to return.

        Returns
        -------
        list[RankedItem]
            Ranked by frequency descending.
        """
        if not terms:
            return []

        normalized = [self._normalizer.normalize(t) for t in terms if t.strip()]
        if not normalized:
            return []

        counter = Counter(normalized)
        total = len(normalized)

        result: list[RankedItem] = []
        for term, count in counter.most_common():
            if count < min_count:
                continue
            result.append(
                RankedItem(
                    name=term,
                    count=count,
                    percentage=round(count / total * 100, 1),
                ),
            )
            if len(result) >= max_results:
                break

        return result

    @staticmethod
    def co_occurrence_clusters(
        items: list[str],
        min_cluster_size: int = 2,
    ) -> dict[str, list[RankedItem]]:
        """Group terms by shared normalized prefix clusters.

        For now this returns a simple ``"all"`` cluster with ranked
        items. Future versions can implement proper co-occurrence
        grouping.
        """
        clusterer = Clusterer()
        ranked = clusterer.cluster_and_rank(items, min_count=min_cluster_size)
        return {"all": ranked} if ranked else {}
