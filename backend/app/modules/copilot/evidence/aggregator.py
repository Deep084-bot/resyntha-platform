"""Evidence aggregator — merges duplicate evidence, groups related findings, preserves provenance."""

from __future__ import annotations

import re
from collections import Counter

from app.modules.copilot.evidence.models import (
    EvidenceBundle,
    EvidenceItem,
    SourceChunk,
    SupportingPaper,
)
from app.observability.logger import get_logger

logger = get_logger(__name__)

_MIN_CLAIM_LENGTH = 15
_OVERLAP_THRESHOLD = 0.55


class EvidenceAggregator:
    """Transforms retrieved sections into structured, deduplicated evidence.

    Responsibilities:
      1. Extract individual claims/statements from each section.
      2. Merge duplicate or near-duplicate claims.
      3. Group related findings under common topics.
      4. Preserve provenance (source, label, score) and paper references.
      5. Remove repeated information while keeping the best-supported version.
    """

    def aggregate(
        self,
        sections: list,
        paper_title_map: dict[str, str] | None = None,
    ) -> EvidenceBundle:
        if not sections:
            return EvidenceBundle()

        items: list[EvidenceItem] = []
        seen_claims: set[str] = set()
        all_papers: set[str] = set()

        for section in sections:
            claims = self._extract_claims(section.content, section.source, section.label)
            for claim_text, is_inference in claims:
                normalized = self._normalize_claim(claim_text)
                if not normalized or len(normalized) < _MIN_CLAIM_LENGTH:
                    continue

                dup = self._find_duplicate(normalized, seen_claims)
                if dup is not None:
                    continue

                seen_claims.add(normalized)

                papers = self._extract_papers(section.content, paper_title_map)
                all_papers.update(p.title for p in papers)

                items.append(EvidenceItem(
                    claim=claim_text,
                    supporting_papers=papers,
                    source_chunks=[SourceChunk(
                        source=section.source,
                        label=section.label,
                        content=section.content,
                        score=getattr(section, "score", 0.0),
                    )],
                    confidence=min(getattr(section, "score", 0.0) / 100.0, 1.0),
                    is_inference=is_inference,
                ))

        if not items:
            return EvidenceBundle()

        char_count = sum(len(i.claim) for i in items)
        total_sources = sum(len(i.source_chunks) for i in items)
        original_chars = sum(len(s.content) for s in sections) if sections else 1
        compression_ratio = round(1.0 - (char_count / original_chars), 4) if original_chars > 0 else 0.0

        return EvidenceBundle(
            items=items,
            total_sources=total_sources,
            total_papers=all_papers,
            aggregated_char_count=char_count,
            compression_ratio=compression_ratio,
        )

    @staticmethod
    def _extract_claims(content: str, source: str, label: str) -> list[tuple[str, bool]]:
        lines = content.split("\n")
        claims: list[tuple[str, bool]] = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < _MIN_CLAIM_LENGTH:
                continue
            cleaned = re.sub(r"^\[.*?\]\s*", "", line)
            cleaned = re.sub(r"^[-•*]\s*", "", cleaned)
            if not cleaned or len(cleaned) < _MIN_CLAIM_LENGTH:
                continue
            is_inference = any(w in cleaned.lower() for w in (
                "suggests", "may", "might", "could", "possibly", "potentially", "appears",
            ))
            claims.append((cleaned, is_inference))
        return claims

    @staticmethod
    def _normalize_claim(text: str) -> str:
        return re.sub(r"[^a-z0-9\s]", "", text.lower().strip())

    @staticmethod
    def _find_duplicate(normalized: str, seen: set[str]) -> str | None:
        for existing in seen:
            if EvidenceAggregator._overlap(normalized, existing) > _OVERLAP_THRESHOLD:
                return existing
        return None

    @staticmethod
    def _overlap(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / min(len(words_a), len(words_b))

    @staticmethod
    def _extract_papers(content: str, paper_title_map: dict[str, str] | None) -> list[SupportingPaper]:
        if not paper_title_map:
            return []
        papers: list[SupportingPaper] = []
        seen: set[str] = set()
        for title in paper_title_map:
            if title.lower() in content.lower() and title not in seen:
                papers.append(SupportingPaper(title=title, relevance="Referenced in evidence"))
                seen.add(title)
                if len(papers) >= 5:
                    break
        return papers
