from __future__ import annotations

from typing import Any

from app.modules.intelligence.aggregation.models import (
    CollaborationSection,
    DatasetSection,
    InstitutionSection,
    LandscapeResult,
    MethodologySection,
    NetworkSection,
    TechnologySection,
    TemporalSection,
)
from app.modules.intelligence.presentation.renderer import BaseRenderer


class JsonRenderer(BaseRenderer):
    def render(self, landscape: LandscapeResult) -> dict[str, Any]:
        result: dict[str, Any] = {}
        self._add_if_nonempty(result, "overview", self._overview(landscape.overview))
        self._add_if_nonempty(result, "institutions", self._institutions(landscape.institutions))
        self._add_if_nonempty(result, "methodologies", self._methodologies(landscape.methodologies))
        self._add_if_nonempty(result, "technologies", self._technologies(landscape.technologies))
        self._add_if_nonempty(result, "datasets", self._datasets(landscape.datasets))
        self._add_if_nonempty(result, "temporal", self._temporal(landscape.temporal))
        self._add_if_nonempty(result, "collaborations", self._collaborations(landscape.collaborations))
        self._add_if_nonempty(result, "observations", self._observations(landscape.observations))
        return result

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _add_if_nonempty(target: dict, key: str, value: Any) -> None:
        if value:
            target[key] = value

    @staticmethod
    def _yes(d: dict) -> bool:
        return bool(d)

    # ── Overview ─────────────────────────────────────────────────

    @staticmethod
    def _overview(o) -> dict | None:
        result = {
            "total_papers": o.total_papers,
            "years_covered": o.years_covered,
            "total_institutions": o.total_institutions,
            "total_methodologies": o.total_methodologies,
            "total_technologies": o.total_technologies,
            "total_datasets": o.total_datasets,
            "total_authors": o.total_authors,
        }
        return result if any(v for v in result.values()) else None

    # ── Institutions ─────────────────────────────────────────────

    @staticmethod
    def _institutions(sec: InstitutionSection) -> dict | None:
        if not sec.total and not sec.top_institutions:
            return None

        return {
            "total": sec.total,
            "type_distribution": sec.type_distribution,
            "top_institutions": [
                {
                    "name": e.name,
                    "type": e.type,
                    "paper_count": e.paper_count,
                    "author_count": e.author_count,
                }
                for e in sec.top_institutions
            ],
        }

    # ── Methodologies ────────────────────────────────────────────

    @staticmethod
    def _methodologies(sec: MethodologySection) -> dict | None:
        if not sec.total and not sec.top_methodologies:
            return None

        return {
            "total": sec.total,
            "methodologies": [
                {
                    "name": e.name,
                    "paper_count": e.paper_count,
                    "technique_count": e.technique_count,
                    "techniques": e.techniques,
                }
                for e in sec.top_methodologies
            ],
        }

    # ── Technologies ─────────────────────────────────────────────

    @staticmethod
    def _technologies(sec: TechnologySection) -> dict | None:
        if not sec.total and not sec.top_technologies:
            return None

        return {
            "total": sec.total,
            "top_technologies": [
                {"name": name, "paper_count": count}
                for name, count in sec.top_technologies
            ],
            "first_appearance_by_year": {
                k: v for k, v in sec.first_appearance_by_year.items()
                if v is not None
            },
            "diversity": {
                "total_technologies": sec.diversity.total,
                "papers_with_technology": sec.diversity.papers_with_entity,
                "avg_papers_per_technology": sec.diversity.avg_papers_per_entity,
            },
        }

    # ── Datasets ─────────────────────────────────────────────────

    @staticmethod
    def _datasets(sec: DatasetSection) -> dict | None:
        if not sec.total and not sec.top_datasets:
            return None

        return {
            "total": sec.total,
            "top_datasets": [
                {"name": name, "paper_count": count}
                for name, count in sec.top_datasets
            ],
            "diversity": {
                "total_datasets": sec.diversity.total,
                "papers_with_dataset": sec.diversity.papers_with_entity,
                "avg_papers_per_dataset": sec.diversity.avg_papers_per_entity,
            },
        }

    # ── Temporal ─────────────────────────────────────────────────

    @staticmethod
    def _temporal(sec: TemporalSection) -> dict | None:
        if not sec.papers_per_year and not sec.total_papers:
            return None
        return {
            "years_covered": sec.years_covered,
            "total_papers": sec.total_papers,
            "papers_per_year": sec.papers_per_year,
        }

    # ── Collaborations ───────────────────────────────────────────

    @staticmethod
    def _network(net: NetworkSection) -> dict:
        return {
            "total_nodes": net.total_nodes,
            "total_edges": net.total_edges,
            "degree_centrality": net.degree_centrality,
            "top_by_centrality": [
                {"name": name, "centrality": round(score, 4)}
                for name, score in net.top_by_centrality
            ],
        }

    @staticmethod
    def _collaborations(sec: CollaborationSection) -> dict | None:
        inst = sec.institution_network
        auth = sec.author_network
        if not inst.total_nodes and not auth.total_nodes:
            return None

        result: dict[str, Any] = {}
        if inst.total_nodes:
            result["institution_network"] = JsonRenderer._network(inst)
            result["institution_collaborations"] = [
                {"source": a, "target": b, "weight": w}
                for a, b, w in sec.top_institution_collaborations
            ]
        if auth.total_nodes:
            result["author_network"] = JsonRenderer._network(auth)
            result["author_collaborations"] = [
                {"source": a, "target": b, "weight": w}
                for a, b, w in sec.top_author_collaborations
            ]
        return result if result else None

    # ── Observations ─────────────────────────────────────────────

    @staticmethod
    def _observations(observations) -> list | None:
        if not observations:
            return None
        return [
            {
                "category": o.category,
                "label": o.label,
                "value": o.value,
            }
            for o in observations
        ]
