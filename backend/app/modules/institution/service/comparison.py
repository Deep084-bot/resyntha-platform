"""Institution Comparison 2.0 — extended comparison with strengths, weaknesses, and overlap."""

from __future__ import annotations

import uuid
from collections import Counter

from fastapi import HTTPException, status

from app.modules.institution.domain.models import (
    CollaborationEntry,
    EntityCount,
    InstitutionComparisonDetail,
    PaperEntry,
    YearlyTrend,
)
from app.modules.intelligence.graph.api.service import GraphApiService
from app.modules.intelligence.graph.models import InstitutionNode, ResearchGraph


class InstitutionComparisonService:
    def __init__(self, graph_service: GraphApiService) -> None:
        self._graph_service = graph_service

    def compare(
        self,
        investigation_id: uuid.UUID,
        institution_names: list[str],
    ) -> list[InstitutionComparisonDetail]:
        if len(institution_names) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least two institution names are required for comparison",
            )
        if len(institution_names) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comparison is limited to at most 5 institutions",
            )

        graph = self._graph_service.get_raw_graph(investigation_id)
        details: list[InstitutionComparisonDetail] = []
        all_nodes: list[tuple[str, InstitutionNode]] = []

        for name in institution_names:
            node = graph.institutions.get(name)
            if node is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Institution '{name}' not found",
                )
            all_nodes.append((name, node))

        for name, node in all_nodes:
            detail = self._build_comparison_detail(graph, name, node, all_nodes)
            details.append(detail)

        return details

    def _build_comparison_detail(
        self,
        graph: ResearchGraph,
        name: str,
        node: InstitutionNode,
        all_institutions: list[tuple[str, InstitutionNode]],
    ) -> InstitutionComparisonDetail:
        papers = [graph.papers[pid] for pid in node.paper_ids if pid in graph.papers]
        paper_count = len(papers)
        citation_count = sum(p.citation_count or 0 for p in papers)
        total_authors = len(node.author_names)
        avg_citations = round(citation_count / max(paper_count, 1), 2)

        research_domains: Counter[str] = Counter()
        technologies: Counter[str] = Counter()
        methodologies: Counter[str] = Counter()
        datasets: Counter[str] = Counter()
        yearly: Counter[int] = Counter()

        for paper in papers:
            for rd in paper.research_domains:
                research_domains[rd] += 1
            for t in paper.technologies:
                technologies[t.name] += 1
            for m in paper.methodologies:
                methodologies[m.name] += 1
            for d in paper.datasets:
                datasets[d.name] += 1
            if paper.year is not None:
                yearly[paper.year] += 1

        growth_rate = 0.0
        sorted_years = sorted(yearly.items())
        if len(sorted_years) >= 2:
            prev = sorted_years[-2][1]
            curr = sorted_years[-1][1]
            growth_rate = (curr - prev) / max(prev, 1)

        research_diversity_score = round(len(research_domains) / max(paper_count, 1), 4)

        collaboration_score = 0.0
        centrality = graph.services.centrality
        if centrality is not None:
            scores = centrality.degree_centrality("institution")
            collaboration_score = round(scores.get(name, 0.0), 4)

        all_other_techs: set[str] = set()
        all_other_methods: set[str] = set()
        all_other_domains: set[str] = set()
        all_other_datasets: set[str] = set()

        for other_name, other_node in all_institutions:
            if other_name == name:
                continue
            other_pids = [pid for pid in other_node.paper_ids if pid in graph.papers]
            other_papers = [graph.papers[pid] for pid in other_pids]
            for p in other_papers:
                for t in p.technologies:
                    all_other_techs.add(t.name)
                for m in p.methodologies:
                    all_other_methods.add(m.name)
                for rd in p.research_domains:
                    all_other_domains.add(rd)
                for d in p.datasets:
                    all_other_datasets.add(d.name)

        strengths = self._compute_strengths(
            paper_count,
            citation_count,
            avg_citations,
            growth_rate,
            research_diversity_score,
            collaboration_score,
        )
        weaknesses = self._compute_weaknesses(
            paper_count,
            citation_count,
            avg_citations,
            growth_rate,
            research_diversity_score,
            collaboration_score,
        )

        specializations = [
            EntityCount(name=rd, count=c) for rd, c in research_domains.most_common(5)
        ]

        sorted_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)
        top_papers = [
            PaperEntry(
                id=p.id,
                title=p.title,
                year=p.year,
                citation_count=p.citation_count,
                venue=p.venue,
                authors=[a.name for a in p.authors],
                research_domains=p.research_domains,
            )
            for p in sorted_papers[:5]
        ]

        collaboration_counts: Counter[str] = Counter()
        if centrality is not None:
            for a, b, w in centrality.collaboration_edges():
                if a == name:
                    collaboration_counts[b] += w
                elif b == name:
                    collaboration_counts[a] += w

        return InstitutionComparisonDetail(
            name=name,
            type=node.type.value,
            total_papers=paper_count,
            total_citations=citation_count,
            total_authors=total_authors,
            avg_citations=avg_citations,
            growth_rate=round(growth_rate, 4),
            research_diversity_score=research_diversity_score,
            collaboration_score=collaboration_score,
            strengths=strengths,
            weaknesses=weaknesses,
            specializations=specializations,
            top_papers=top_papers,
            yearly_trends=[YearlyTrend(year=y, paper_count=c) for y, c in sorted_years],
            collaborating_institutions=[
                CollaborationEntry(institution_name=inst, joint_paper_count=count)
                for inst, count in collaboration_counts.most_common(10)
            ],
        )

    @staticmethod
    def _compute_strengths(
        paper_count: int,
        citation_count: int,
        avg_citations: float,
        growth_rate: float,
        research_diversity: float,
        collaboration_score: float,
    ) -> list[str]:
        strengths: list[str] = []
        if paper_count > 10:
            strengths.append("High publication output")
        if citation_count > 100:
            strengths.append("High citation impact")
        if avg_citations > 10:
            strengths.append("High average citations per paper")
        if growth_rate > 0.5:
            strengths.append("Fast publication growth")
        if research_diversity > 0.3:
            strengths.append("Broad research diversity")
        if collaboration_score > 0.5:
            strengths.append("Strong collaboration network")
        return strengths

    @staticmethod
    def _compute_weaknesses(
        paper_count: int,
        citation_count: int,
        avg_citations: float,
        growth_rate: float,
        research_diversity: float,
        collaboration_score: float,
    ) -> list[str]:
        weaknesses: list[str] = []
        if paper_count < 3:
            weaknesses.append("Low publication output")
        if citation_count < 10:
            weaknesses.append("Low citation impact")
        if avg_citations < 3:
            weaknesses.append("Below-average citations per paper")
        if growth_rate < 0:
            weaknesses.append("Declining publication trend")
        if research_diversity < 0.1:
            weaknesses.append("Narrow research focus")
        if collaboration_score < 0.1:
            weaknesses.append("Limited collaboration network")
        return weaknesses
