"""Context builder — collects and prioritises investigation artifacts."""

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.modules.artifact.domain.models import Artifact, ArtifactType
from app.modules.artifact.repository.repository import ArtifactRepository
from app.modules.extraction.repository.repository import ExtractionRepository
from app.modules.paper.domain.models import Paper
from app.modules.paper.repository.repository import PaperRepository
from app.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────

_TOKEN_BUDGET = 7000
_CHARS_PER_TOKEN = 4
_CONTEXT_CHAR_LIMIT = _TOKEN_BUDGET * _CHARS_PER_TOKEN  # 28000

_ARTIFACT_PRIORITY: list[ArtifactType] = [
    ArtifactType.KNOWLEDGE_PACKAGE,
    ArtifactType.RESEARCH_GAP_REPORT,
    ArtifactType.RESEARCH_LANDSCAPE,
    ArtifactType.PAPER_COLLECTION,
    ArtifactType.VALIDATED_COLLECTION,
]

_ARTIFACT_CHAR_BUDGETS: dict[ArtifactType, int] = {
    ArtifactType.KNOWLEDGE_PACKAGE: 8000,
    ArtifactType.RESEARCH_GAP_REPORT: 5000,
    ArtifactType.RESEARCH_LANDSCAPE: 4000,
    ArtifactType.PAPER_COLLECTION: 6000,
    ArtifactType.VALIDATED_COLLECTION: 3000,
}

_MAX_PAPER_SUMMARIES = 15


@dataclass
class ArtifactSection:
    artifact_type: ArtifactType
    label: str
    summary: str
    raw_payload: dict | None


@dataclass
class BuiltContext:
    sections: list[ArtifactSection] = field(default_factory=list)
    paper_title_map: dict[str, str] = field(default_factory=dict)
    char_count: int = 0
    truncated: bool = False

    def to_text(self) -> str:
        parts: list[str] = []
        for section in self.sections:
            parts.append(f"=== {section.label} ===\n{section.summary}")
        text = "\n\n".join(parts)
        if self.truncated:
            text += "\n[Context truncated due to length]"
        return text


class ContextBuilder:
    """Collects investigation artifacts, deduplicates, and budgets token usage.

    Priority order:
        1. Knowledge Package
        2. Research Gap Report
        3. Research Landscape
        4. Paper Collection
        5. Validated Collection
    """

    def __init__(self, session: Session) -> None:
        self._artifact_repo = ArtifactRepository(session)
        self._paper_repo = PaperRepository(session)
        self._extraction_repo = ExtractionRepository(session)
        self._session = session

    def build(self, investigation_id: uuid.UUID) -> BuiltContext:
        context = BuiltContext()
        remaining = _CONTEXT_CHAR_LIMIT

        all_artifacts = self._artifact_repo.list_by_investigation(investigation_id)
        papers = self._paper_repo.list_by_investigation(investigation_id)
        extract_map = self._build_extract_map(investigation_id)

        context.paper_title_map = {p.title: str(p.id) for p in papers if p.title}

        for atype in _ARTIFACT_PRIORITY:
            if remaining <= 0:
                context.truncated = True
                break

            artifact = self._latest_artifact(all_artifacts, atype)
            if artifact is None or artifact.payload is None:
                continue

            budget = min(_ARTIFACT_CHAR_BUDGETS.get(atype, 4000), remaining)
            section = self._build_section(artifact, papers, extract_map, budget)
            if section is None:
                continue

            context.sections.append(section)
            context.char_count += len(section.summary)
            remaining -= len(section.summary)

        return context

    def get_papers_context(self, papers: Sequence[Paper], limit: int = _MAX_PAPER_SUMMARIES) -> str:
        lines: list[str] = []
        for p in papers[:limit]:
            authors = ", ".join(getattr(p, "authors", []) or [])
            abstract = (p.abstract or "")[:400]
            doi = p.doi or "N/A"
            lines.append(f"Title: {p.title}\nAuthors: {authors}\nAbstract: {abstract}\nDOI: {doi}")
        return "\n\n".join(lines)

    def _build_extract_map(self, investigation_id: uuid.UUID) -> dict[str, dict]:
        extractions = (
            self._extraction_repo.list_by_investigation(investigation_id)
            if hasattr(self._extraction_repo, "list_by_investigation")
            else []
        )
        result: dict[str, dict] = {}
        for ext in extractions:
            paper_id = str(getattr(ext, "paper_id", ""))
            if paper_id:
                result[paper_id] = {
                    "findings": getattr(ext, "key_findings", None) or [],
                    "methodology": getattr(ext, "methodology", None) or "",
                    "limitations": getattr(ext, "limitations", None) or [],
                    "future_work": getattr(ext, "future_work", None) or [],
                }
        return result

    @staticmethod
    def _latest_artifact(
        artifacts: Sequence[Artifact],
        atype: ArtifactType,
    ) -> Artifact | None:
        matches = [a for a in artifacts if a.artifact_type == atype and a.status.value == "ready"]
        if not matches:
            return None
        return max(matches, key=lambda a: a.created_at)

    def _build_section(
        self,
        artifact: Artifact,
        papers: Sequence[Paper],
        extract_map: dict[str, dict],
        char_budget: int,
    ) -> ArtifactSection | None:
        payload = artifact.payload
        if not payload:
            return None

        label = artifact.artifact_type.value.replace("_", " ").title()

        if artifact.artifact_type == ArtifactType.KNOWLEDGE_PACKAGE:
            summary = self._summarise_knowledge_package(payload, char_budget)
        elif artifact.artifact_type == ArtifactType.RESEARCH_GAP_REPORT:
            summary = self._summarise_gap_report(payload, char_budget)
        elif artifact.artifact_type == ArtifactType.RESEARCH_LANDSCAPE:
            summary = self._summarise_landscape(payload, papers, char_budget)
        elif artifact.artifact_type in (
            ArtifactType.PAPER_COLLECTION,
            ArtifactType.VALIDATED_COLLECTION,
        ):
            summary = self._summarise_paper_collection(payload, papers, char_budget)
        else:
            summary = json.dumps(payload, indent=1)[:char_budget]

        return ArtifactSection(
            artifact_type=artifact.artifact_type,
            label=label,
            summary=summary,
            raw_payload=payload,
        )

    def _summarise_knowledge_package(self, payload: dict, budget: int) -> str:
        parts: list[str] = []
        for key in ("research_questions", "key_findings", "summary", "methodology", "conclusions"):
            value = payload.get(key)
            if value:
                if isinstance(value, list):
                    text = "\n".join(
                        f"- {v}" if isinstance(v, str) else json.dumps(v) for v in value[:10]
                    )
                elif isinstance(value, dict):
                    text = json.dumps(value, indent=1)[:1500]
                else:
                    text = str(value)
                parts.append(f"{key.replace('_', ' ').title()}:\n{text}")

        result = "\n\n".join(parts)
        if len(result) > budget:
            result = result[:budget]
            last_break = result.rfind("\n")
            if last_break > 0:
                result = result[:last_break]
        return result

    def _summarise_gap_report(self, payload: dict, budget: int) -> str:
        parts: list[str] = []
        gaps = payload.get("research_gaps") or payload.get("gaps") or []
        if isinstance(gaps, list):
            for gap in gaps[:8]:
                if isinstance(gap, str):
                    parts.append(f"- {gap}")
                elif isinstance(gap, dict):
                    desc = gap.get("description") or gap.get("gap") or json.dumps(gap)
                    parts.append(f"- {str(desc)[:500]}")

        opportunities = payload.get("opportunities") or payload.get("future_directions") or []
        if isinstance(opportunities, list) and opportunities:
            parts.append("\nOpportunities:")
            for opp in opportunities[:5]:
                if isinstance(opp, str):
                    parts.append(f"- {opp}")
                elif isinstance(opp, dict):
                    parts.append(f"- {str(opp.get('description', opp))[:300]}")

        result = "\n".join(parts) if parts else json.dumps(payload, indent=1)[:budget]
        if len(result) > budget:
            result = result[:budget]
            last_break = result.rfind("\n")
            if last_break > 0:
                result = result[:last_break]
        return result

    def _summarise_landscape(self, payload: dict, papers: Sequence[Paper], budget: int) -> str:
        parts: list[str] = []

        for key in (
            "research_domains",
            "methodologies",
            "technologies",
            "datasets",
            "evaluation_metrics",
        ):
            items = payload.get(key, [])
            if items:
                names = []
                for item in items[:8]:
                    if isinstance(item, dict):
                        names.append(str(item.get("name", item)))
                    elif isinstance(item, str):
                        names.append(item)
                if names:
                    parts.append(f"{key.replace('_', ' ').title()}: {', '.join(names)}")

        authors = payload.get("top_authors", [])
        if authors:
            author_names = []
            for a in authors[:5]:
                if isinstance(a, dict):
                    author_names.append(str(a.get("name", a)))
                elif isinstance(a, str):
                    author_names.append(a)
            if author_names:
                parts.append(f"Key Authors: {', '.join(author_names)}")

        institutions = payload.get("institutions", [])
        if institutions:
            inst_names = []
            for i in institutions[:5]:
                if isinstance(i, dict):
                    inst_names.append(str(i.get("name", i)))
                elif isinstance(i, str):
                    inst_names.append(i)
            if inst_names:
                parts.append(f"Institutions: {', '.join(inst_names)}")

        result = "\n".join(parts) if parts else json.dumps(payload, indent=1)[:budget]
        if len(result) > budget:
            result = result[:budget]
            last_break = result.rfind("\n")
            if last_break > 0:
                result = result[:last_break]
        return result

    def _summarise_paper_collection(
        self, payload: dict, papers: Sequence[Paper], budget: int
    ) -> str:
        papers_data = payload.get("papers") or payload.get("results") or payload.get("items") or []
        if not papers_data:
            return self.get_papers_context(papers, limit=10)

        parts: list[str] = []
        if isinstance(papers_data, list):
            for p in papers_data[:10]:
                if isinstance(p, dict):
                    title = p.get("title", "Untitled")
                    authors = p.get("authors") or p.get("author", "")
                    if isinstance(authors, list):
                        authors = ", ".join(str(a) for a in authors[:3])
                    abstract = str(p.get("abstract", "") or "")[:300]
                    doi = p.get("doi", "N/A")
                    parts.append(
                        f"Title: {title}\nAuthors: {authors}\nAbstract: {abstract}\nDOI: {doi}"
                    )
                elif isinstance(p, str):
                    parts.append(f"- {p}")

        result = "\n\n".join(parts) if parts else json.dumps(payload, indent=1)[:budget]
        if len(result) > budget:
            result = result[:budget]
            last_break = result.rfind("\n")
            if last_break > 0:
                result = result[:last_break]
        return result
