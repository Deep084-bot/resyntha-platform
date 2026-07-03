from __future__ import annotations

from app.modules.intelligence.analyzers.base import BaseAnalyzer
from app.modules.intelligence.analyzers.models import AnalyzerResult


class CollaborationAnalyzer(BaseAnalyzer):
    analyzer_name = "collaboration"

    def analyze(self) -> AnalyzerResult:
        graph = self.graph
        config = self.config
        centrality = graph.services.centrality
        max_results = config.max_results_per_analyzer

        author_edges = centrality.co_authorship_edges()
        author_edges.sort(key=lambda x: x[2], reverse=True)

        inst_edges = centrality.collaboration_edges()
        inst_edges.sort(key=lambda x: x[2], reverse=True)

        author_centrality = centrality.degree_centrality("author")
        inst_centrality = centrality.degree_centrality("institution")

        top_authors = sorted(
            author_centrality.items(), key=lambda x: x[1], reverse=True,
        )[:max_results]
        top_institutions = sorted(
            inst_centrality.items(), key=lambda x: x[1], reverse=True,
        )[:max_results]

        return AnalyzerResult(
            analyzer_name=self.analyzer_name,
            data={
                "institution_collaborations": inst_edges[:max_results],
                "author_collaborations": author_edges[:max_results],
                "institution_network": {
                    "total_institutions": len(graph.institutions),
                    "total_collaborations": len(inst_edges),
                    "degree_centrality": inst_centrality,
                    "top_by_centrality": top_institutions,
                },
                "author_network": {
                    "total_authors": len(graph.authors),
                    "total_collaborations": len(author_edges),
                    "degree_centrality": author_centrality,
                    "top_by_centrality": top_authors,
                },
            },
        )
