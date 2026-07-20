from __future__ import annotations

import uuid
from collections import Counter

from fastapi import HTTPException, status

from app.modules.institution.domain.models import (
    AuthorEntry,
    CollaborationEntry,
    EntityCount,
    InstitutionProfile,
    PaperEntry,
    YearlyTrend,
)
from app.modules.intelligence.graph.api.service import GraphApiService
from app.modules.intelligence.graph.models import InstitutionNode, ResearchGraph


class InstitutionProfileService:
    def __init__(self, graph_service: GraphApiService) -> None:
        self._graph_service = graph_service

    def list_profiles(self, investigation_id: uuid.UUID) -> list[InstitutionProfile]:
        graph = self._graph_service.get_raw_graph(investigation_id)
        if not graph.institutions:
            return []
        profiles = [self._build_profile(graph, node) for node in graph.institutions.values()]
        profiles.sort(key=lambda p: p.total_papers, reverse=True)
        return profiles

    def get_profile(self, investigation_id: uuid.UUID, name: str) -> InstitutionProfile:
        graph = self._graph_service.get_raw_graph(investigation_id)
        node = graph.institutions.get(name)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Institution '{name}' not found",
            )
        return self._build_profile(graph, node)

    def compare(
        self,
        investigation_id: uuid.UUID,
        institution_names: list[str],
    ) -> list[InstitutionProfile]:
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
        profiles: list[InstitutionProfile] = []
        for name in institution_names:
            node = graph.institutions.get(name)
            if node is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Institution '{name}' not found",
                )
            profiles.append(self._build_profile(graph, node))
        return profiles

    def _build_profile(
        self,
        graph: ResearchGraph,
        node: InstitutionNode,
    ) -> InstitutionProfile:
        papers = [graph.papers[pid] for pid in node.paper_ids if pid in graph.papers]

        total_citations = sum(p.citation_count or 0 for p in papers)
        total_authors = len(node.author_names)
        author_name_set = set(node.author_names)

        research_domains: Counter[str] = Counter()
        technologies: Counter[str] = Counter()
        datasets: Counter[str] = Counter()
        methodologies: Counter[str] = Counter()
        yearly: Counter[int] = Counter()
        author_paper_counts: Counter[str] = Counter()
        co_author_counts: Counter[str] = Counter()

        for paper in papers:
            for rd in paper.research_domains:
                research_domains[rd] += 1
            for t in paper.technologies:
                technologies[t.name] += 1
            for d in paper.datasets:
                datasets[d.name] += 1
            for m in paper.methodologies:
                methodologies[m.name] += 1
            if paper.year is not None:
                yearly[paper.year] += 1

            for author in paper.authors:
                author_paper_counts[author.name] += 1
                if author.name not in author_name_set:
                    co_author_counts[author.name] += 1

        top_author_entries = [
            AuthorEntry(
                name=a_name,
                paper_count=count,
                affiliated_institutions=[
                    inst.name
                    for inst in (
                        graph.authors[a_name].affiliated_institutions
                        if a_name in graph.authors
                        else []
                    )
                ],
            )
            for a_name, count in author_paper_counts.most_common(10)
        ]

        sorted_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)
        top_paper_entries = [
            PaperEntry(
                id=p.id,
                title=p.title,
                year=p.year,
                citation_count=p.citation_count,
                venue=p.venue,
                authors=[a.name for a in p.authors],
                research_domains=p.research_domains,
            )
            for p in sorted_papers[:10]
        ]

        collaboration_counts: Counter[str] = Counter()
        centrality = graph.services.centrality
        if centrality is not None:
            for a, b, w in centrality.collaboration_edges():
                if a == node.name:
                    collaboration_counts[b] += w
                elif b == node.name:
                    collaboration_counts[a] += w

        collaborating_entries = [
            CollaborationEntry(institution_name=inst, joint_paper_count=count)
            for inst, count in collaboration_counts.most_common(10)
        ]

        co_author_entries = [
            AuthorEntry(name=a_name, paper_count=count)
            for a_name, count in co_author_counts.most_common(10)
        ]

        return InstitutionProfile(
            name=node.name,
            type=node.type.value,
            total_papers=len(papers),
            total_authors=total_authors,
            total_citations=total_citations,
            research_domains=[
                EntityCount(name=rd, count=c) for rd, c in research_domains.most_common()
            ],
            technologies=[EntityCount(name=t, count=c) for t, c in technologies.most_common()],
            datasets=[EntityCount(name=d, count=c) for d, c in datasets.most_common()],
            methodologies=[EntityCount(name=m, count=c) for m, c in methodologies.most_common()],
            top_authors=top_author_entries,
            top_papers=top_paper_entries,
            yearly_trends=[YearlyTrend(year=y, paper_count=c) for y, c in sorted(yearly.items())],
            collaborating_institutions=collaborating_entries,
            co_authors=co_author_entries,
        )
