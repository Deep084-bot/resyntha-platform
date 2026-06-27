"""Retrieval service — orchestrates the full paper-fetch pipeline.

Runs all configured providers concurrently, normalises their results
into a common representation, deduplicates, and ranks.  Persistence
is handled by the :class:`RetrievalWorkflow`.
"""

import asyncio
from collections.abc import Sequence

from app.modules.retrieval.deduplication.deduplicator import deduplicate
from app.modules.retrieval.domain.paper import Paper
from app.modules.retrieval.normalization.normalizer import (
    normalize_arxiv,
    normalize_semantic_scholar,
)
from app.modules.retrieval.providers.arxiv import ArxivProvider
from app.modules.retrieval.providers.semantic_scholar import (
    SemanticScholarProvider,
)
from app.modules.retrieval.ranking.scorer import rank as rank_papers
from app.observability.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    """Search external providers, normalise, deduplicate, and rank papers."""

    def __init__(
        self,
        semantic_scholar: SemanticScholarProvider | None = None,
        arxiv: ArxivProvider | None = None,
    ) -> None:
        self._ss = semantic_scholar or SemanticScholarProvider()
        self._arxiv = arxiv or ArxivProvider()

    async def retrieve(
        self,
        query: str,
        paper_limit: int = 10,
    ) -> Sequence[Paper]:
        """Search providers, normalise, deduplicate, and rank.

        Returns a score-descending list of canonical ``Paper`` objects
        without persisting them.
        """
        logger.info(
            "retrieval_started", query=query, paper_limit=paper_limit
        )

        ss_task = self._ss.search(query, paper_limit)
        arxiv_task = self._arxiv.search(query, paper_limit)
        ss_results, arxiv_results = await asyncio.gather(
            ss_task, arxiv_task
        )

        logger.info(
            "retrieval_providers_done",
            semantic_scholar=len(ss_results),
            arxiv=len(arxiv_results),
        )

        papers: list[Paper] = []
        for raw in ss_results:
            papers.append(normalize_semantic_scholar(raw))
        for raw in arxiv_results:
            papers.append(normalize_arxiv(raw))

        papers = deduplicate(papers)
        papers = rank_papers(papers)

        logger.info("retrieval_completed", total=len(papers))
        return papers
