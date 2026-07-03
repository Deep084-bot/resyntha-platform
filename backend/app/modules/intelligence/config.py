"""Intelligence-level configuration.

Thresholds and limits that control analyzer behaviour.  Every field
has a sensible default so that the engine works out of the box with
no configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntelligenceConfig:
    """Configuration for the Intelligence Engine and its analyzers.

    Parameters
    ----------
    min_methodology_frequency:
        Minimum papers a methodology must appear in to be included
        in ranked output.
    min_dataset_frequency:
        Minimum papers a dataset must appear in to be included.
    min_technology_frequency:
        Minimum papers a technology must appear in to be included.
    min_author_frequency:
        Minimum papers an author must appear in to be included.
    trend_window_years:
        Number of recent years considered for trend detection.
    co_occurrence_threshold:
        Minimum co-occurrence count to be considered meaningful.
    novelty_std_threshold:
        Number of standard deviations from the mean a paper must be
        to be flagged as novel.
    max_results_per_analyzer:
        Maximum number of items returned in any single ranked list.
    """

    min_methodology_frequency: int = 1
    min_dataset_frequency: int = 1
    min_technology_frequency: int = 1
    min_author_frequency: int = 1
    trend_window_years: int = 3
    co_occurrence_threshold: int = 1
    novelty_std_threshold: float = 2.0
    max_results_per_analyzer: int = 20
