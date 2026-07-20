"""Institution search and topic search.

All search is performed in-memory against the ResearchGraph.
No external search index, no database tables.
"""

from __future__ import annotations

import uuid
from collections import Counter
from difflib import SequenceMatcher

from app.modules.institution.domain.models import (
    AuthorEntry,
    InstitutionSearchResult,
    PaperEntry,
    TopicSearchResult,
)
from app.modules.intelligence.graph.api.service import GraphApiService
from app.modules.intelligence.graph.models import ResearchGraph


class InstitutionSearchService:
    def __init__(self, graph_service: GraphApiService) -> None:
        self._graph_service = graph_service

    # ── Institution name search ─────────────────────────────────

    def search(
        self,
        investigation_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[InstitutionSearchResult]:
        if not query or not query.strip():
            return []

        graph = self._graph_service.get_raw_graph(investigation_id)
        normalized_query = query.strip().lower()

        scored: list[tuple[float, int, str]] = []
        for name, node in graph.institutions.items():
            score = self._compute_name_score(name, normalized_query)
            if score > 0:
                paper_count = len(node.paper_ids)
                citation_count = self._count_citations(graph, node.paper_ids)
                scored.append((score, paper_count, name))

        scored.sort(key=lambda x: (-x[0], -x[1]))
        top_names = scored[:limit]

        results: list[InstitutionSearchResult] = []
        for score, paper_count, name in top_names:
            node = graph.institutions[name]
            citation_count = self._count_citations(graph, node.paper_ids)
            results.append(
                InstitutionSearchResult(
                    name=name,
                    type=node.type.value,
                    paper_count=len(node.paper_ids),
                    author_count=len(node.author_names),
                    citation_count=citation_count,
                    relevance_score=round(score, 4),
                )
            )

        return results

    @staticmethod
    def _compute_name_score(name: str, query: str) -> float:
        lower_name = name.lower()
        lower_query = query.lower()

        if lower_name == lower_query:
            return 1.0
        if lower_name.startswith(lower_query):
            return 0.9

        # Acronym match: "MIT" ↔ "Massachusetts Institute of Technology"
        name_tokens = lower_name.split()
        stop_words = {"of", "the", "and", "for", "in", "at", "on", "by", "a", "an"}
        if len(lower_query) >= 2 and len(name_tokens) >= 2:
            acronym = "".join(t[0] for t in name_tokens if t and t not in stop_words)
            if acronym == lower_query:
                return 0.85

        if len(lower_query) >= 3 and lower_query in lower_name:
            return 0.7

        if len(lower_query) >= 2:
            query_tokens = lower_query.split()
            match_count = sum(1 for qt in query_tokens if any(qt in nt for nt in name_tokens))
            if match_count > 0:
                ratio = match_count / max(len(query_tokens), 1)
                return 0.4 * ratio

        ratio = SequenceMatcher(None, lower_name, lower_query).ratio()
        if ratio > 0.6:
            return ratio * 0.3

        return 0.0

    # ── Topic search ────────────────────────────────────────────

    def topic_search(
        self,
        investigation_id: uuid.UUID,
        topic: str,
        limit: int = 10,
    ) -> list[TopicSearchResult]:
        if not topic or not topic.strip():
            return []

        graph = self._graph_service.get_raw_graph(investigation_id)
        normalized_topic = topic.strip().lower()

        topic_paper_ids = self._find_topic_papers(graph, normalized_topic)
        if not topic_paper_ids:
            return []

        institution_scores: dict[str, tuple[int, int]] = {}
        for pid in topic_paper_ids:
            paper = graph.papers.get(pid)
            if paper is None:
                continue
            for inst in paper.institutions:
                cur_papers, cur_citations = institution_scores.get(inst.name, (0, 0))
                institution_scores[inst.name] = (
                    cur_papers + 1,
                    cur_citations + (paper.citation_count or 0),
                )

        ranked = sorted(institution_scores.items(), key=lambda x: -x[1][0])
        top = ranked[:limit]

        results: list[TopicSearchResult] = []
        for inst_name, (paper_count, citation_count) in top:
            relevant_papers = []
            author_counter: Counter[str] = Counter()

            for pid in topic_paper_ids:
                paper = graph.papers.get(pid)
                if paper and any(i.name == inst_name for i in paper.institutions):
                    relevant_papers.append(paper)
                    for a in paper.authors:
                        author_counter[a.name] += 1

            relevant_papers.sort(key=lambda p: p.citation_count or 0, reverse=True)

            results.append(
                TopicSearchResult(
                    institution_name=inst_name,
                    paper_count=paper_count,
                    citation_count=citation_count,
                    top_papers=[
                        PaperEntry(
                            id=p.id,
                            title=p.title,
                            year=p.year,
                            citation_count=p.citation_count,
                            venue=p.venue,
                            authors=[a.name for a in p.authors],
                            research_domains=p.research_domains,
                        )
                        for p in relevant_papers[:5]
                    ],
                    top_authors=[
                        AuthorEntry(name=a, paper_count=c) for a, c in author_counter.most_common(5)
                    ],
                    relevance_score=round(paper_count / max(len(topic_paper_ids), 1), 4),
                )
            )

        return results

    @staticmethod
    def _find_topic_papers(graph: ResearchGraph, topic: str) -> set[str]:
        matching: set[str] = set()
        lower_topic = topic.lower()

        for pid, paper in graph.papers.items():
            for rd in paper.research_domains:
                if lower_topic in rd.lower():
                    matching.add(pid)
                    break
            else:
                for t in paper.technologies:
                    if lower_topic in t.name.lower():
                        matching.add(pid)
                        break
                else:
                    for d in paper.datasets:
                        if lower_topic in d.name.lower():
                            matching.add(pid)
                            break
                    else:
                        for m in paper.methodologies:
                            if lower_topic in m.name.lower():
                                matching.add(pid)
                                break

        return matching

    @staticmethod
    def _count_citations(graph: ResearchGraph, paper_ids: list[str]) -> int:
        return sum(
            graph.papers[pid].citation_count or 0 for pid in paper_ids if pid in graph.papers
        )

    # ── Multi-criteria filtering ────────────────────────────────

    def filter_institutions(
        self,
        investigation_id: uuid.UUID,
        *,
        research_domains: list[str] | None = None,
        technologies: list[str] | None = None,
        datasets: list[str] | None = None,
        methodologies: list[str] | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        min_citations: int | None = None,
        min_papers: int | None = None,
        limit: int = 50,
    ) -> list[InstitutionSearchResult]:
        graph = self._graph_service.get_raw_graph(investigation_id)
        results: list[InstitutionSearchResult] = []

        for name, node in graph.institutions.items():
            papers = [graph.papers[pid] for pid in node.paper_ids if pid in graph.papers]

            if not self._matches_filters(
                papers,
                research_domains=research_domains,
                technologies=technologies,
                datasets=datasets,
                methodologies=methodologies,
                min_year=min_year,
                max_year=max_year,
                min_citations=min_citations,
                min_papers=min_papers,
            ):
                continue

            citation_count = sum(p.citation_count or 0 for p in papers)
            results.append(
                InstitutionSearchResult(
                    name=name,
                    type=node.type.value,
                    paper_count=len(papers),
                    author_count=len(node.author_names),
                    citation_count=citation_count,
                    relevance_score=1.0,
                )
            )

        results.sort(key=lambda r: r.paper_count, reverse=True)
        return results[:limit]

    @staticmethod
    def _matches_filters(
        papers: list,
        *,
        research_domains: list[str] | None,
        technologies: list[str] | None,
        datasets: list[str] | None,
        methodologies: list[str] | None,
        min_year: int | None,
        max_year: int | None,
        min_citations: int | None,
        min_papers: int | None,
    ) -> bool:
        if min_papers is not None and len(papers) < min_papers:
            return False
        if min_citations is not None:
            total = sum(p.citation_count or 0 for p in papers)
            if total < min_citations:
                return False

        for paper in papers:
            if min_year is not None and (paper.year is None or paper.year < min_year):
                continue
            if max_year is not None and (paper.year is None or paper.year > max_year):
                continue

            if research_domains and not any(
                any(rd.lower() in dr.lower() for dr in paper.research_domains)
                for rd in research_domains
            ):
                continue
            if technologies and not any(
                any(t.lower() in tech.name.lower() for tech in paper.technologies)
                for t in technologies
            ):
                continue
            if datasets and not any(
                any(d.lower() in ds.name.lower() for ds in paper.datasets) for d in datasets
            ):
                continue
            if methodologies and not any(
                any(m.lower() in meth.name.lower() for meth in paper.methodologies)
                for m in methodologies
            ):
                continue

            return True

        return False
