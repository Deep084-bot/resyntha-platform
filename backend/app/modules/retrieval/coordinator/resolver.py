"""DuplicateResolver — identifies and removes duplicate papers.

Strategy (in order of precedence):
1. DOI match (case-insensitive)
2. External ID match (arXiv, Semantic Scholar, OpenAlex)
3. Exact title match (case-insensitive)
4. Normalised title match (lowercased, stripped, punctuation removed)
5. URL normalisation match
"""

import re
from collections.abc import Sequence

from app.modules.retrieval.domain.paper import Paper


class DuplicateResolver:
    """Identify duplicate papers using multiple strategies."""

    def __call__(self, papers: Sequence[Paper]) -> list[Paper]:
        return self.resolve(papers)

    def resolve(self, papers: Sequence[Paper]) -> list[Paper]:
        seen_dois: set[str] = set()
        seen_external_ids: set[tuple[str, str]] = set()
        seen_titles: set[str] = set()
        seen_normalized: set[str] = set()
        seen_urls: set[str] = set()
        unique: list[Paper] = []

        for paper in papers:
            if self._is_duplicate(
                paper,
                seen_dois,
                seen_external_ids,
                seen_titles,
                seen_normalized,
                seen_urls,
            ):
                continue

            if paper.doi:
                seen_dois.add(paper.doi.lower())
            for ext_id in self._external_ids(paper):
                seen_external_ids.add(ext_id)
            seen_titles.add(paper.title.lower().strip())
            seen_normalized.add(self._normalize_title(paper.title))
            normalized_url = self._normalize_url(paper.url)
            if normalized_url:
                seen_urls.add(normalized_url)
            unique.append(paper)

        return unique

    def _is_duplicate(
        self,
        paper: Paper,
        seen_dois: set[str],
        seen_external_ids: set[tuple[str, str]],
        seen_titles: set[str],
        seen_normalized: set[str],
        seen_urls: set[str],
    ) -> bool:
        if paper.doi and paper.doi.lower() in seen_dois:
            return True
        for ext_id in self._external_ids(paper):
            if ext_id in seen_external_ids:
                return True
        title_key = paper.title.lower().strip()
        if title_key in seen_titles:
            return True
        if self._normalize_title(paper.title) in seen_normalized:
            return True
        normalized_url = self._normalize_url(paper.url)
        if normalized_url and normalized_url in seen_urls:
            return True
        return False

    def _external_ids(self, paper: Paper) -> list[tuple[str, str]]:
        ids: list[tuple[str, str]] = []
        ext_ids = paper.metadata.get("external_ids", {}) if isinstance(paper.metadata, dict) else {}
        for namespace in ("arxiv", "semantic_scholar", "openalex"):
            value = ext_ids.get(namespace)
            if value:
                ids.append((namespace, str(value).lower().strip()))
        return ids

    def _normalize_url(self, url: str | None) -> str | None:
        if not url:
            return None
        normalized = url.lower().strip()
        normalized = re.sub(r"^https?://", "", normalized)
        normalized = normalized.rstrip("/")
        return normalized

    @staticmethod
    def _normalize_title(title: str) -> str:
        normalized = title.lower().strip()
        normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized
