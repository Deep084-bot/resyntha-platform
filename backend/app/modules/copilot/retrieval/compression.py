"""Context compression — merges overlapping chunks and deduplicates."""

from __future__ import annotations

from app.modules.copilot.retrieval.models import RetrievedSection

_OVERLAP_THRESHOLD = 0.60


class ContextCompressor:
    """Merges overlapping chunks and removes duplicates.

    Strategy:
    1. Sort by score descending.
    2. For each chunk, compare with already-selected chunks.
    3. If content overlap > threshold, keep the higher-scoring one.
    4. If chunks are similar but about different sections, keep both.
    """

    def compress(
        self,
        sections: list[RetrievedSection],
    ) -> list[RetrievedSection]:
        if not sections:
            return sections

        sorted_sections = sorted(sections, key=lambda s: s.score, reverse=True)
        compressed: list[RetrievedSection] = []

        for section in sorted_sections:
            is_dup = False
            for existing in compressed:
                if self._is_redundant(section, existing):
                    is_dup = True
                    break
            if not is_dup:
                compressed.append(section)

        return compressed

    @staticmethod
    def _is_redundant(a: RetrievedSection, b: RetrievedSection) -> bool:
        if a.label != b.label:
            return False
        overlap = ContextCompressor._content_overlap(a.content, b.content)
        return overlap > _OVERLAP_THRESHOLD

    @staticmethod
    def _content_overlap(x: str, y: str) -> float:
        if not x or not y:
            return 0.0
        set_x = set(x.lower().split())
        set_y = set(y.lower().split())
        if not set_x or not set_y:
            return 0.0
        intersection = set_x & set_y
        return len(intersection) / min(len(set_x), len(set_y))
