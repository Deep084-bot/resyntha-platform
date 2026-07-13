from __future__ import annotations

from app.modules.intelligence.aggregation.models import (
    DatasetSection,
    InstitutionSection,
    LandscapeResult,
    MethodologySection,
    TechnologySection,
    TemporalSection,
)
from app.modules.intelligence.presentation.renderer import BaseRenderer


def _td(row: list[str]) -> str:
    return "| " + " | ".join(row) + " |"


def _section(level: int, title: str) -> str:
    return f"{'#' * level} {title}"


class MarkdownRenderer(BaseRenderer):
    def render(self, landscape: LandscapeResult) -> str:
        parts: list[str] = [_section(1, "Research Landscape"), ""]

        self._overview(parts, landscape)
        self._institutions(parts, landscape.institutions)
        self._methodologies(parts, landscape.methodologies)
        self._technologies(parts, landscape.technologies)
        self._datasets(parts, landscape.datasets)
        self._temporal(parts, landscape.temporal)
        self._collaborations(parts, landscape.collaborations)
        self._observations(parts, landscape.observations)

        return "\n".join(parts).strip() + "\n"

    # ── Overview ─────────────────────────────────────────────────

    @staticmethod
    def _overview(parts: list[str], landscape: LandscapeResult) -> None:
        o = landscape.overview
        if o.total_papers == 0 and not o.years_covered:
            return

        parts.append(_section(2, "Overview"))
        parts.append("")
        rows = []
        if o.total_papers:
            rows.append(["Total Papers", str(o.total_papers)])
        if o.years_covered:
            span = _format_years(o.years_covered)
            rows.append(["Years Covered", span])
        if o.total_institutions:
            rows.append(["Total Institutions", str(o.total_institutions)])
        if o.total_methodologies:
            rows.append(["Total Methodologies", str(o.total_methodologies)])
        if o.total_technologies:
            rows.append(["Total Technologies", str(o.total_technologies)])
        if o.total_datasets:
            rows.append(["Total Datasets", str(o.total_datasets)])
        if o.total_authors:
            rows.append(["Total Authors", str(o.total_authors)])

        if rows:
            parts.append(_td(["Metric", "Value"]))
            parts.append(_td(["---", "---"]))
            for row in rows:
                parts.append(_td(row))
            parts.append("")

    # ── Institutions ─────────────────────────────────────────────

    @staticmethod
    def _institutions(parts: list[str], sec: InstitutionSection) -> None:
        if not sec.top_institutions:
            return

        parts.append(_section(2, "Institutions"))
        parts.append("")
        parts.append(_td(["Institution", "Type", "Papers", "Authors"]))
        parts.append(_td(["---", "---", "---", "---"]))
        for e in sec.top_institutions:
            parts.append(_td([e.name, e.type, str(e.paper_count), str(e.author_count)]))
        parts.append("")

        if sec.type_distribution:
            parts.append(_section(3, "Type Distribution"))
            parts.append("")
            parts.append(_td(["Type", "Count"]))
            parts.append(_td(["---", "---"]))
            for t, count in sorted(sec.type_distribution.items()):
                parts.append(_td([t, str(count)]))
            parts.append("")

    # ── Methodologies ────────────────────────────────────────────

    @staticmethod
    def _methodologies(parts: list[str], sec: MethodologySection) -> None:
        if not sec.top_methodologies:
            return

        parts.append(_section(2, "Methodologies"))
        parts.append("")
        parts.append(_td(["Methodology", "Papers", "Techniques"]))
        parts.append(_td(["---", "---", "---"]))
        for e in sec.top_methodologies:
            techs = ", ".join(e.techniques) if e.techniques else "—"
            parts.append(_td([e.name, str(e.paper_count), techs]))
        parts.append("")

    # ── Technologies ─────────────────────────────────────────────

    @staticmethod
    def _technologies(parts: list[str], sec: TechnologySection) -> None:
        if not sec.top_technologies:
            return

        parts.append(_section(2, "Technologies"))
        parts.append("")
        parts.append(_td(["Technology", "Papers", "First Appearance"]))
        parts.append(_td(["---", "---", "---"]))
        for name, count in sec.top_technologies:
            first = sec.first_appearance_by_year.get(name)
            first_str = str(first) if first is not None else "—"
            parts.append(_td([name, str(count), first_str]))
        parts.append("")

        d = sec.diversity
        if d.total:
            parts.append(
                f"**Diversity:** {d.total} technologies, "
                f"{d.papers_with_entity} papers, "
                f"{d.avg_papers_per_entity} avg papers per technology"
            )
            parts.append("")

    # ── Datasets ─────────────────────────────────────────────────

    @staticmethod
    def _datasets(parts: list[str], sec: DatasetSection) -> None:
        if not sec.top_datasets:
            return

        parts.append(_section(2, "Datasets"))
        parts.append("")
        parts.append(_td(["Dataset", "Papers"]))
        parts.append(_td(["---", "---"]))
        for name, count in sec.top_datasets:
            parts.append(_td([name, str(count)]))
        parts.append("")

        d = sec.diversity
        if d.total:
            parts.append(
                f"**Diversity:** {d.total} datasets, "
                f"{d.papers_with_entity} papers, "
                f"{d.avg_papers_per_entity} avg papers per dataset"
            )
            parts.append("")

    # ── Temporal Trends ──────────────────────────────────────────

    @staticmethod
    def _temporal(parts: list[str], sec: TemporalSection) -> None:
        if not sec.papers_per_year:
            return

        parts.append(_section(2, "Temporal Trends"))
        parts.append("")
        parts.append(_td(["Year", "Papers"]))
        parts.append(_td(["---", "---"]))
        for year, count in sorted(sec.papers_per_year.items()):
            parts.append(_td([str(year), str(count)]))
        parts.append("")

    # ── Collaborations ───────────────────────────────────────────

    @staticmethod
    def _collaborations(parts: list[str], sec) -> None:
        inst_net = sec.institution_network
        auth_net = sec.author_network
        if not inst_net.total_nodes and not auth_net.total_nodes:
            return

        parts.append(_section(2, "Collaborations"))
        parts.append("")

        if inst_net.total_nodes:
            parts.append(_section(3, "Institution Network"))
            parts.append("")
            parts.append(f"- **Nodes:** {inst_net.total_nodes}")
            parts.append(f"- **Edges:** {inst_net.total_edges}")
            if inst_net.top_by_centrality:
                top = inst_net.top_by_centrality[0]
                parts.append(f"- **Most Central:** {top[0]} (centrality {top[1]:.2f})")
            parts.append("")

            if sec.top_institution_collaborations:
                parts.append(_td(["Institution A", "Institution B", "Papers"]))
                parts.append(_td(["---", "---", "---"]))
                for a, b, w in sec.top_institution_collaborations:
                    parts.append(_td([a, b, str(w)]))
                parts.append("")

        if auth_net.total_nodes:
            parts.append(_section(3, "Author Network"))
            parts.append("")
            parts.append(f"- **Nodes:** {auth_net.total_nodes}")
            parts.append(f"- **Edges:** {auth_net.total_edges}")
            if auth_net.top_by_centrality:
                top = auth_net.top_by_centrality[0]
                parts.append(f"- **Most Central:** {top[0]} (centrality {top[1]:.2f})")
            parts.append("")

            if sec.top_author_collaborations:
                parts.append(_td(["Author A", "Author B", "Papers"]))
                parts.append(_td(["---", "---", "---"]))
                for a, b, w in sec.top_author_collaborations:
                    parts.append(_td([a, b, str(w)]))
                parts.append("")

    # ── Observations ─────────────────────────────────────────────

    @staticmethod
    def _observations(parts: list[str], observations) -> None:
        if not observations:
            return

        parts.append(_section(2, "Key Observations"))
        parts.append("")
        for obs in observations:
            parts.append(f"- **{obs.label}:** {obs.value}")
        parts.append("")


def _format_years(years: list[int]) -> str:
    if not years:
        return ""
    if len(years) == 1:
        return str(years[0])
    return f"{years[0]}–{years[-1]}"
