"""MetadataMerger — merges duplicate papers from multiple providers.

When two providers return the same paper, the merger preserves the
best available information from each source and tracks field-level
provenance in ``paper.metadata["provenance"]``.
"""

from collections.abc import Sequence

from app.modules.retrieval.coordinator.resolver import DuplicateResolver
from app.modules.retrieval.domain.paper import Paper


class MetadataMerger:
    """Merge papers that represent the same publication from different providers."""

    def __init__(self) -> None:
        self._resolver = DuplicateResolver()

    def merge(self, papers: Sequence[Paper]) -> list[Paper]:
        groups = self._group(papers)
        merged: list[Paper] = []
        for group in groups:
            merged.append(self._merge_group(group))
        return merged

    def _group(self, papers: Sequence[Paper]) -> list[list[Paper]]:
        """Group papers that are duplicates into lists."""
        seen: list[Paper] = []
        groups: list[list[Paper]] = []
        index_map: dict[int, int] = {}  # paper position in `papers` → group index

        for i, paper in enumerate(papers):
            found = False
            for j, representative in enumerate(seen):
                if self._resolver._is_duplicate(
                    paper,
                    {representative.doi.lower()} if representative.doi else set(),
                    set(self._resolver._external_ids(representative)),
                    {representative.title.lower().strip()},
                    {DuplicateResolver._normalize_title(representative.title)},
                    (
                        {self._resolver._normalize_url(representative.url)}
                        if representative.url
                        else set()
                    ),
                ):
                    groups[index_map[j]].append(paper)
                    found = True
                    break
            if not found:
                groups.append([paper])
                index_map[i] = len(groups) - 1
                seen.append(paper)

        return groups

    def _merge_group(self, group: list[Paper]) -> Paper:
        """Merge a group of duplicate papers into a single canonical paper."""
        if len(group) == 1:
            paper = group[0].model_copy()
            paper.metadata = {**paper.metadata, "provenance": self._build_provenance(paper, group)}
            return paper

        primary = group[0].model_copy()
        providers_seen = {primary.source} if primary.source else set()

        for other in group[1:]:
            if other.source:
                providers_seen.add(other.source)
            self._merge_field(primary, other, "title")
            self._merge_field(primary, other, "abstract")
            self._merge_field(primary, other, "doi")
            self._merge_field(primary, other, "url")
            self._merge_field(primary, other, "venue")
            self._merge_field(primary, other, "year")
            self._merge_field(primary, other, "citation_count")
            self._merge_authors(primary, other)

        primary.metadata = {
            **primary.metadata,
            "provenance": self._build_provenance(primary, group),
            "merged_from": sorted(providers_seen),
        }
        return primary

    def _merge_field(self, primary: Paper, other: Paper, field: str) -> None:
        """Merge a single field from *other* into *primary* if primary has no value."""
        primary_val = getattr(primary, field, None)
        other_val = getattr(other, field, None)
        if not primary_val and other_val:
            setattr(primary, field, other_val)

    def _merge_authors(self, primary: Paper, other: Paper) -> None:
        """Merge author lists, preferring the longer list."""
        if len(other.authors) > len(primary.authors):
            primary.authors = other.authors

    def _build_provenance(self, primary: Paper, group: list[Paper]) -> dict[str, list[str]]:
        """Build a provenance map: field_name → [provider_names]."""
        provenance: dict[str, list[str]] = {}
        for paper in group:
            source = paper.source or "unknown"
            for field in primary.model_fields:
                val = getattr(paper, field, None)
                if val is not None and field != "metadata":
                    provenance.setdefault(field, []).append(source)
        # Deduplicate provider names per field
        return {k: list(dict.fromkeys(v)) for k, v in provenance.items()}
