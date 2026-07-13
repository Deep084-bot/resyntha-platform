"""Chunking pipeline — splits investigation artifacts into overlapping chunks."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.copilot.chunking.models import Chunk
from app.observability.logger import get_logger

logger = get_logger(__name__)

_MAX_CHUNK_CHARS = 800
_OVERLAP_CHARS = 80


class ChunkingPipeline:
    """Breaks investigation artifacts into overlapping, metadata-rich chunks.

    Respects section boundaries: each logical section (Key Findings,
    Methodologies, Datasets, etc.) is chunked independently.  Long
    sections are split with overlap to preserve context.
    """

    def chunk_all(
        self,
        investigation_id: uuid.UUID,
        artifacts: Sequence[Artifact],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        for artifact in artifacts:
            if artifact.status.value != "ready" or not artifact.payload:
                continue
            atype = artifact.artifact_type
            aid = artifact.id
            if atype == ArtifactType.KNOWLEDGE_PACKAGE:
                chunks.extend(
                    self._chunk_knowledge_package(investigation_id, aid, artifact.payload)
                )
            elif atype == ArtifactType.RESEARCH_LANDSCAPE:
                chunks.extend(self._chunk_landscape(investigation_id, aid, artifact.payload))
            elif atype == ArtifactType.RESEARCH_GAP_REPORT:
                chunks.extend(self._chunk_gap_report(investigation_id, aid, artifact.payload))
            elif atype in (ArtifactType.PAPER_COLLECTION, ArtifactType.VALIDATED_COLLECTION):
                chunks.extend(
                    self._chunk_paper_collection(investigation_id, aid, artifact.payload, atype)
                )
        return chunks

    # ── Knowledge Package ───────────────────────────────────────

    def _chunk_knowledge_package(
        self, investigation_id: uuid.UUID, artifact_id: uuid.UUID, payload: dict
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        papers_data = payload.get("papers", [])
        if not isinstance(papers_data, list):
            return chunks

        for p in papers_data[:50]:
            if not isinstance(p, dict):
                continue
            paper_id = p.get("paper_id") or p.get("id")
            title = p.get("paper_title", p.get("title", ""))
            prefix = f"[{title}] " if title else ""

            sections = {
                "Key Findings": self._fmt_list(p.get("key_findings", []), prefix),
                "Methodologies": [f"{prefix}{p.get('methodology', '')}"]
                if p.get("methodology")
                else [],
                "Limitations": self._fmt_list(p.get("limitations", []), prefix),
                "Future Work": self._fmt_list(p.get("future_work", []), prefix),
                "Technologies": self._fmt_list(p.get("relevant_techniques", []), prefix),
                "Research Questions": self._fmt_list(p.get("research_questions", []), prefix),
                "Summary": [f"{prefix}{p.get('summary', '')}"] if p.get("summary") else [],
            }

            for label, items in sections.items():
                if not items:
                    continue
                content = "\n".join(items)
                metadata = {"paper_title": title} if title else {}
                chunks.extend(
                    self._split(
                        investigation_id,
                        artifact_id,
                        paper_id,
                        "Knowledge Package",
                        label,
                        content,
                        metadata,
                    )
                )

        return chunks

    # ── Landscape ───────────────────────────────────────────────

    def _chunk_landscape(
        self, investigation_id: uuid.UUID, artifact_id: uuid.UUID, payload: dict
    ) -> list[Chunk]:
        chunks: list[Chunk] = []

        section_map = {
            "Research Domains": "research_domains",
            "Methodologies": "methodologies",
            "Datasets": "datasets",
            "Evaluation Metrics": "evaluation_metrics",
            "Technologies": "keywords",
            "Authors": "top_authors",
            "Applications": "applications",
            "Limitations": "limitations",
            "Future Work": "future_work",
        }

        for label, key in section_map.items():
            items = payload.get(key, [])
            names = self._names_from(items)
            if names:
                content = ", ".join(names)
                chunks.extend(
                    self._split(
                        investigation_id,
                        artifact_id,
                        None,
                        "Landscape",
                        label,
                        content,
                    )
                )

        return chunks

    # ── Gap Report ──────────────────────────────────────────────

    def _chunk_gap_report(
        self, investigation_id: uuid.UUID, artifact_id: uuid.UUID, payload: dict
    ) -> list[Chunk]:
        chunks: list[Chunk] = []

        gaps = payload.get("gaps", [])
        if isinstance(gaps, list) and gaps:
            lines: list[str] = []
            for g in gaps[:15]:
                if not isinstance(g, dict):
                    continue
                title = g.get("title", "") or g.get("description", "")
                desc = g.get("description", "")
                cat = g.get("category", "")
                line = f"[{cat}] {title}" if cat else title
                if desc and desc != title:
                    line += f": {desc[:300]}"
                if line.strip():
                    lines.append(line)
            if lines:
                chunks.extend(
                    self._split(
                        investigation_id,
                        artifact_id,
                        None,
                        "Gap Report",
                        "Research Gaps",
                        "\n".join(lines),
                    )
                )

        recommendations = payload.get("recommendations", [])
        if isinstance(recommendations, list) and recommendations:
            rec_lines = [str(r) for r in recommendations[:8] if str(r).strip()]
            if rec_lines:
                chunks.extend(
                    self._split(
                        investigation_id,
                        artifact_id,
                        None,
                        "Gap Report",
                        "Recommendations",
                        "\n".join(rec_lines),
                    )
                )

        return chunks

    # ── Paper Collection ────────────────────────────────────────

    def _chunk_paper_collection(
        self,
        investigation_id: uuid.UUID,
        artifact_id: uuid.UUID,
        payload: dict,
        atype: ArtifactType,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        papers_data = payload.get("papers") or payload.get("results") or payload.get("items") or []
        if not isinstance(papers_data, list):
            return chunks

        source = "Paper Collection"
        if atype == ArtifactType.VALIDATED_COLLECTION:
            source = "Validated Collection"

        for p in papers_data[:10]:
            if not isinstance(p, dict):
                continue
            title = p.get("title", "Untitled")
            authors = p.get("authors") or p.get("author", "")
            if isinstance(authors, list):
                authors = ", ".join(str(a) for a in authors[:3])
            abstract = str(p.get("abstract", "") or "")[:500]
            doi = p.get("doi", "N/A")
            content = f"Title: {title}\nAuthors: {authors}\nAbstract: {abstract}\nDOI: {doi}"
            chunks.extend(
                self._split(
                    investigation_id,
                    artifact_id,
                    None,
                    source,
                    "Papers",
                    content,
                    metadata={"paper_title": title},
                )
            )

        return chunks

    # ── Internal helpers ────────────────────────────────────────

    def _split(
        self,
        investigation_id: uuid.UUID,
        artifact_id: uuid.UUID | None,
        paper_id: uuid.UUID | None,
        source: str,
        section: str,
        content: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        if not content.strip():
            return []
        metadata = metadata or {}
        if len(content) <= _MAX_CHUNK_CHARS:
            return [
                Chunk(
                    investigation_id=investigation_id,
                    artifact_id=artifact_id,
                    paper_id=paper_id,
                    source=source,
                    section=section,
                    chunk_index=0,
                    content=content,
                    metadata=metadata,
                )
            ]

        chunks: list[Chunk] = []
        idx = 0
        start = 0
        while start < len(content):
            end = min(start + _MAX_CHUNK_CHARS, len(content))
            if end < len(content):
                # Try to break at a newline
                newline_break = content.rfind("\n", start + _MAX_CHUNK_CHARS // 2, end)
                if newline_break > start:
                    end = newline_break
            chunk_text = content[start:end]
            chunks.append(
                Chunk(
                    investigation_id=investigation_id,
                    artifact_id=artifact_id,
                    paper_id=paper_id,
                    source=source,
                    section=section,
                    chunk_index=idx,
                    content=chunk_text,
                    metadata=metadata,
                )
            )
            idx += 1
            if end >= len(content):
                break
            # Overlap: rewind by _OVERLAP_CHARS
            start = end - _OVERLAP_CHARS

        return chunks

    @staticmethod
    def _fmt_list(items: list, prefix: str = "") -> list[str]:
        if not isinstance(items, list):
            return []
        result: list[str] = []
        for item in items:
            s = str(item).strip()
            if s:
                result.append(f"{prefix}{s}")
        return result

    @staticmethod
    def _names_from(items: list) -> list[str]:
        if not isinstance(items, list):
            return []
        names: list[str] = []
        for item in items[:15]:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    names.append(str(name))
            elif isinstance(item, str):
                names.append(item)
        return names
