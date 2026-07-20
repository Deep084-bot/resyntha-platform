"""Institution ranking, intelligence, and trend analysis.

All computations are dynamic from the ResearchGraph.
No persistence, no external indices.
"""

from __future__ import annotations

import uuid
from collections import Counter

from app.modules.institution.domain.models import (
    EntityCount,
    InstitutionIntelligence,
    InstitutionRankingEntry,
    InstitutionTrend,
    YearlyTrend,
)
from app.modules.intelligence.graph.api.service import GraphApiService
from app.modules.intelligence.graph.models import ResearchGraph


class InstitutionAnalyticsService:
    def __init__(self, graph_service: GraphApiService) -> None:
        self._graph_service = graph_service

    # ── Ranking ────────────────────────────────────────────────

    def rank(
        self,
        investigation_id: uuid.UUID,
        criterion: str = "publication_count",
        limit: int = 10,
    ) -> list[InstitutionRankingEntry]:
        graph = self._graph_service.get_raw_graph(investigation_id)
        entries = [
            self._build_ranking_entry(graph, name, node)
            for name, node in graph.institutions.items()
        ]

        sort_key = self._sort_key_fn(criterion)
        entries.sort(key=sort_key, reverse=True)

        for i, entry in enumerate(entries[:limit]):
            entry.rank = i + 1

        return entries[:limit]

    @staticmethod
    def _sort_key_fn(criterion: str):
        mapping = {
            "publication_count": lambda e: e.paper_count,
            "citation_count": lambda e: e.citation_count,
            "avg_citations": lambda e: e.avg_citations,
            "growth_rate": lambda e: e.growth_rate,
            "technology_diversity": lambda e: e.technology_diversity,
            "research_diversity": lambda e: e.research_diversity,
            "collaboration_score": lambda e: e.collaboration_score,
        }
        return mapping.get(criterion, lambda e: e.paper_count)

    # ── Intelligence ───────────────────────────────────────────

    def get_intelligence(self, investigation_id: uuid.UUID) -> InstitutionIntelligence:
        graph = self._graph_service.get_raw_graph(investigation_id)
        entries = [
            self._build_ranking_entry(graph, name, node)
            for name, node in graph.institutions.items()
        ]

        if not entries:
            return InstitutionIntelligence()

        entries.sort(key=lambda e: e.paper_count, reverse=True)
        top = entries[:10]

        emerging = [e for e in entries if e.growth_rate > 0.3]
        emerging.sort(key=lambda e: e.growth_rate, reverse=True)

        collaborative = sorted(entries, key=lambda e: e.collaboration_score, reverse=True)[:10]

        growing = sorted(entries, key=lambda e: e.growth_rate, reverse=True)[:10]

        tech_leaders = sorted(entries, key=lambda e: e.technology_diversity, reverse=True)[:10]
        dataset_leaders = sorted(entries, key=lambda e: e.paper_count, reverse=True)[:10]
        methodology_leaders = sorted(entries, key=lambda e: e.research_diversity, reverse=True)[:10]

        return InstitutionIntelligence(
            top_institutions=top,
            emerging_institutions=emerging[:10],
            most_collaborative=collaborative,
            fastest_growing=growing,
            technology_leaders=tech_leaders,
            dataset_leaders=dataset_leaders,
            methodology_leaders=methodology_leaders,
        )

    # ── Trends ─────────────────────────────────────────────────

    def get_trends(
        self,
        investigation_id: uuid.UUID,
        names: list[str],
    ) -> list[InstitutionTrend]:
        graph = self._graph_service.get_raw_graph(investigation_id)
        results: list[InstitutionTrend] = []
        for name in names:
            node = graph.institutions.get(name)
            if node:
                results.append(self._build_trend(graph, name, node))
        return results

    def get_all_trends(self, investigation_id: uuid.UUID) -> list[InstitutionTrend]:
        graph = self._graph_service.get_raw_graph(investigation_id)
        return [self._build_trend(graph, name, node) for name, node in graph.institutions.items()]

    def _build_trend(
        self,
        graph: ResearchGraph,
        name: str,
        node: object,
    ) -> InstitutionTrend:
        papers = [graph.papers[pid] for pid in node.paper_ids if pid in graph.papers]  # type: ignore[attr-defined]

        yearly: Counter[int] = Counter()
        tech_adoption: Counter[str] = Counter()
        research_evolution: Counter[str] = Counter()

        for paper in papers:
            if paper.year is not None:
                yearly[paper.year] += 1
            for t in paper.technologies:
                tech_adoption[t.name] += 1
            for rd in paper.research_domains:
                research_evolution[rd] += 1

        growth_rate = 0.0
        sorted_years = sorted(yearly.items())
        if len(sorted_years) >= 2:
            prev = sorted_years[-2][1]
            curr = sorted_years[-1][1]
            growth_rate = (curr - prev) / max(prev, 1)

        graph_years = graph.years
        is_emerging = False
        if graph_years and sorted_years:
            cutoff = max(graph_years) - 2
            is_emerging = sorted_years[-1][0] >= cutoff and growth_rate > 0

        return InstitutionTrend(
            name=name,
            yearly_publications=[YearlyTrend(year=y, paper_count=c) for y, c in sorted_years],
            growth_rate=round(growth_rate, 4),
            is_emerging=is_emerging,
            technology_adoption=[
                EntityCount(name=t, count=c) for t, c in tech_adoption.most_common(10)
            ],
            research_evolution=[
                EntityCount(name=rd, count=c) for rd, c in research_evolution.most_common(10)
            ],
        )

    # ── Internal helpers ───────────────────────────────────────

    def _build_ranking_entry(
        self,
        graph: ResearchGraph,
        name: str,
        node: object,
    ) -> InstitutionRankingEntry:
        papers = [graph.papers[pid] for pid in node.paper_ids if pid in graph.papers]  # type: ignore[attr-defined]

        paper_count = len(papers)
        citation_count = sum(p.citation_count or 0 for p in papers)
        avg_citations = round(citation_count / max(paper_count, 1), 2)

        technology_names: set[str] = set()
        research_domain_names: set[str] = set()
        yearly: Counter[int] = Counter()

        for paper in papers:
            for t in paper.technologies:
                technology_names.add(t.name)
            for rd in paper.research_domains:
                research_domain_names.add(rd)
            if paper.year is not None:
                yearly[paper.year] += 1

        growth_rate = 0.0
        sorted_years = sorted(yearly.items())
        if len(sorted_years) >= 2:
            prev = sorted_years[-2][1]
            curr = sorted_years[-1][1]
            growth_rate = (curr - prev) / max(prev, 1)

        collaboration_score = 0.0
        centrality = graph.services.centrality
        if centrality is not None:
            scores = centrality.degree_centrality("institution")
            collaboration_score = round(scores.get(name, 0.0), 4)

        return InstitutionRankingEntry(
            name=name,
            type=node.type.value,  # type: ignore[attr-defined]
            paper_count=paper_count,
            citation_count=citation_count,
            avg_citations=avg_citations,
            growth_rate=round(growth_rate, 4),
            technology_diversity=len(technology_names),
            research_diversity=len(research_domain_names),
            collaboration_score=collaboration_score,
            rank=0,
        )
