"""Section extractor — breaks investigation artifacts into logical sections."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.copilot.retrieval.models import RetrievedSection
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)

_MAX_PAPERS_IN_SECTION = 10


class SectionExtractor:
    """Breaks investigation artifacts into logical, retrievable sections."""

    def __init__(self, session: Session) -> None:
        self._artifact_repo = ArtifactRepository(session)
        self._paper_repo = PaperRepository(session)
        self._extraction_repo = ExtractionRepository(session)

    def extract_all(self, investigation_id: uuid.UUID) -> list[RetrievedSection]:
        sections: list[RetrievedSection] = []
        artifacts = self._artifact_repo.list_by_investigation(investigation_id)

        kp = self._latest_ready(artifacts, ArtifactType.KNOWLEDGE_PACKAGE)
        if kp and kp.payload:
            sections.extend(self._extract_knowledge_package(kp))

        landscape = self._latest_ready(artifacts, ArtifactType.RESEARCH_LANDSCAPE)
        if landscape and landscape.payload:
            sections.extend(self._extract_landscape(landscape))

        gap = self._latest_ready(artifacts, ArtifactType.RESEARCH_GAP_REPORT)
        if gap and gap.payload:
            sections.extend(self._extract_gap_report(gap))

        paper_collection = self._latest_ready(artifacts, ArtifactType.PAPER_COLLECTION)
        if paper_collection and paper_collection.payload:
            sections.extend(self._extract_paper_collection(paper_collection))

        validated = self._latest_ready(artifacts, ArtifactType.VALIDATED_COLLECTION)
        if validated and validated.payload:
            sections.extend(self._extract_paper_collection(validated, prefix="Validated "))

        papers = self._paper_repo.list_by_investigation(investigation_id)
        if papers:
            sections.extend(self._extract_papers(papers))

        return sections

    # ── Knowledge Package sections ──────────────────────────────

    @staticmethod
    def _extract_knowledge_package(artifact: Artifact) -> list[RetrievedSection]:
        payload = artifact.payload or {}
        papers_data = payload.get("papers", [])
        if not isinstance(papers_data, list):
            return []

        sections: list[RetrievedSection] = []
        all_findings: list[str] = []
        all_methods: list[str] = []
        all_limitations: list[str] = []
        all_future: list[str] = []
        all_techniques: list[str] = []
        all_questions: list[str] = []
        all_summaries: list[str] = []

        for p in papers_data[:50]:
            if not isinstance(p, dict):
                continue
            title = p.get("paper_title", p.get("title", ""))
            prefix = f"[{title}] " if title else ""

            findings = p.get("key_findings", [])
            if isinstance(findings, list):
                for f in findings[:5]:
                    if isinstance(f, str) and f.strip():
                        all_findings.append(f"{prefix}{f.strip()}")

            methodology = p.get("methodology", "")
            if isinstance(methodology, str) and methodology.strip():
                all_methods.append(f"{prefix}{methodology.strip()}")

            limitations = p.get("limitations", [])
            if isinstance(limitations, list):
                for lim in limitations[:5]:
                    if isinstance(lim, str) and lim.strip():
                        all_limitations.append(f"{prefix}{lim.strip()}")

            future = p.get("future_work", [])
            if isinstance(future, list):
                for fw in future[:5]:
                    if isinstance(fw, str) and fw.strip():
                        all_future.append(f"{prefix}{fw.strip()}")

            techniques = p.get("relevant_techniques", [])
            if isinstance(techniques, list):
                for t in techniques[:5]:
                    if isinstance(t, str) and t.strip():
                        all_techniques.append(f"{prefix}{t.strip()}")

            questions = p.get("research_questions", [])
            if isinstance(questions, list):
                for q in questions[:3]:
                    if isinstance(q, str) and q.strip():
                        all_questions.append(f"{prefix}{q.strip()}")

            summary = p.get("summary", "")
            if isinstance(summary, str) and summary.strip():
                all_summaries.append(f"[{title}] {summary.strip()}" if title else summary.strip())

        if all_findings:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Key Findings",
                    content="\n".join(all_findings),
                )
            )
        if all_methods:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Methodologies",
                    content="\n".join(all_methods),
                )
            )
        if all_limitations:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Limitations",
                    content="\n".join(all_limitations),
                )
            )
        if all_future:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Future Work",
                    content="\n".join(all_future),
                )
            )
        if all_techniques:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Technologies",
                    content="\n".join(all_techniques),
                )
            )
        if all_questions:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Research Questions",
                    content="\n".join(all_questions),
                )
            )
        if all_summaries:
            sections.append(
                RetrievedSection(
                    source="Knowledge Package",
                    label="Summaries",
                    content="\n".join(all_summaries),
                )
            )

        return sections

    # ── Landscape sections ──────────────────────────────────────

    @staticmethod
    def _extract_landscape(artifact: Artifact) -> list[RetrievedSection]:
        payload = artifact.payload or {}
        sections: list[RetrievedSection] = []

        domain_names = SectionExtractor._names_from_ranked(payload.get("research_domains", []))
        if domain_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Research Domains",
                    content=", ".join(domain_names),
                )
            )

        meth_names = SectionExtractor._names_from_ranked(payload.get("methodologies", []))
        if meth_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Methodologies",
                    content=", ".join(meth_names),
                )
            )

        dataset_names = SectionExtractor._names_from_ranked(payload.get("datasets", []))
        if dataset_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Datasets",
                    content=", ".join(dataset_names),
                )
            )

        metric_names = SectionExtractor._names_from_ranked(payload.get("evaluation_metrics", []))
        if metric_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Evaluation Metrics",
                    content=", ".join(metric_names),
                )
            )

        tech_names = SectionExtractor._names_from_ranked(payload.get("keywords", []))
        if tech_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Technologies",
                    content=", ".join(tech_names),
                )
            )

        author_names = SectionExtractor._names_from_ranked(payload.get("top_authors", []))
        if author_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Authors",
                    content=", ".join(author_names),
                )
            )

        app_names = SectionExtractor._names_from_ranked(payload.get("applications", []))
        if app_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Applications",
                    content=", ".join(app_names),
                )
            )

        limitation_names = SectionExtractor._names_from_ranked(payload.get("limitations", []))
        if limitation_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Limitations",
                    content=", ".join(limitation_names),
                )
            )

        future_names = SectionExtractor._names_from_ranked(payload.get("future_work", []))
        if future_names:
            sections.append(
                RetrievedSection(
                    source="Landscape",
                    label="Future Work",
                    content=", ".join(future_names),
                )
            )

        return sections

    # ── Gap Report sections ─────────────────────────────────────

    @staticmethod
    def _extract_gap_report(artifact: Artifact) -> list[RetrievedSection]:
        payload = artifact.payload or {}
        sections: list[RetrievedSection] = []

        gaps = payload.get("gaps", [])
        if isinstance(gaps, list) and gaps:
            gap_lines: list[str] = []
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
                    gap_lines.append(line)
            if gap_lines:
                sections.append(
                    RetrievedSection(
                        source="Gap Report",
                        label="Research Gaps",
                        content="\n".join(gap_lines),
                    )
                )

        recommendations = payload.get("recommendations", [])
        if isinstance(recommendations, list) and recommendations:
            rec_lines = [str(r) for r in recommendations[:8] if str(r).strip()]
            if rec_lines:
                sections.append(
                    RetrievedSection(
                        source="Gap Report",
                        label="Recommendations",
                        content="\n".join(rec_lines),
                    )
                )

        return sections

    # ── Paper Collection sections ───────────────────────────────

    @staticmethod
    def _extract_paper_collection(artifact: Artifact, prefix: str = "") -> list[RetrievedSection]:
        payload = artifact.payload or {}
        papers_data = payload.get("papers") or payload.get("results") or payload.get("items") or []
        if not isinstance(papers_data, list) or not papers_data:
            return []

        lines: list[str] = []
        for p in papers_data[:_MAX_PAPERS_IN_SECTION]:
            if not isinstance(p, dict):
                continue
            title = p.get("title", "Untitled")
            authors = p.get("authors") or p.get("author", "")
            if isinstance(authors, list):
                authors = ", ".join(str(a) for a in authors[:3])
            abstract = str(p.get("abstract", "") or "")[:300]
            doi = p.get("doi", "N/A")
            lines.append(f"Title: {title}\nAuthors: {authors}\nAbstract: {abstract}\nDOI: {doi}")

        if lines:
            sections = [
                RetrievedSection(
                    source=f"{prefix}Paper Collection".strip(),
                    label="Papers",
                    content="\n\n".join(lines),
                )
            ]
            return sections
        return []

    # ── Raw Paper sections (fallback when no paper artifacts) ───

    @staticmethod
    def _extract_papers(papers: Sequence) -> list[RetrievedSection]:
        lines: list[str] = []
        for p in papers[:_MAX_PAPERS_IN_SECTION]:
            title = getattr(p, "title", "Untitled")
            authors_list = getattr(p, "authors", []) or []
            if isinstance(authors_list, list):
                authors = ", ".join(str(a) for a in authors_list[:3])
            else:
                authors = str(authors_list)[:100]
            abstract = (getattr(p, "abstract", "") or "")[:300]
            doi = getattr(p, "doi", "N/A")
            lines.append(f"Title: {title}\nAuthors: {authors}\nAbstract: {abstract}\nDOI: {doi}")
        if not lines:
            return []
        return [
            RetrievedSection(
                source="Papers",
                label="Individual Paper Summaries",
                content="\n\n".join(lines),
            )
        ]

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _latest_ready(artifacts: Sequence[Artifact], atype: ArtifactType) -> Artifact | None:
        matches = [
            a
            for a in artifacts
            if a.artifact_type == atype and a.status.value == "ready" and a.payload
        ]
        if not matches:
            return None
        return max(matches, key=lambda a: a.created_at)

    @staticmethod
    def _names_from_ranked(items: list) -> list[str]:
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
