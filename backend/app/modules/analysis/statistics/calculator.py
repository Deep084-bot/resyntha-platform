"""Statistical computations for the analysis engine.

All methods are stateless and deterministic — given the same input
they always produce the same output.
"""

import statistics
from collections import Counter
from collections.abc import Sequence


class StatisticsCalculator:
    """Pure statistical functions for research landscape computation."""

    @staticmethod
    def compute_average(values: Sequence[float | int]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def compute_median(values: Sequence[float | int]) -> float:
        if not values:
            return 0.0
        try:
            return statistics.median(values)
        except statistics.StatisticsError:
            return 0.0

    @staticmethod
    def frequency_distribution(
        items: Sequence[str],
        normalize: bool = True,
    ) -> dict[str, int]:
        """Return a dict mapping each unique item to its count.

        If *normalize* is True, items are lowercased and stripped
        before counting.
        """
        processed = (s.strip().lower() if normalize and s else s for s in items if s)
        return dict(Counter(processed).most_common())

    @staticmethod
    def top_items(
        items: Sequence[str],
        n: int = 10,
        normalize: bool = True,
    ) -> list[tuple[str, int]]:
        """Return the *n* most frequent items sorted descending."""
        dist = StatisticsCalculator.frequency_distribution(items, normalize=normalize)
        return list(dist.items())[:n]

    @staticmethod
    def flatten_list_of_lists(lists: Sequence[Sequence[str]]) -> list[str]:
        """Flatten a list of string lists into a single list of strings."""
        return [item for sublist in lists if sublist for item in sublist]
