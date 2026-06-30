"""Paper service."""

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.paper.domain.models import InvestigationPaper, Paper, PaperSource
from app.modules.paper.repository.repository import PaperRepository
from app.modules.retrieval.domain.paper import Paper as PaperDTO
from app.observability.logger import get_logger

logger = get_logger(__name__)


class PaperService:
    """Encapsulates paper persistence business logic."""

    def __init__(self, session: Session) -> None:
        self._repository = PaperRepository(session)
        self._session = session

    def persist_retrieved_papers(
        self,
        investigation_id: uuid.UUID,
        papers: Sequence[PaperDTO],
    ) -> list[uuid.UUID]:
        """Persist retrieved canonical papers and attach them to an investigation.

        For each paper in the sequence:

        1. Look up by DOI — reuse if found.
        2. Fall back to exact title lookup — reuse if found.
        3. Create a new ``Paper`` record when neither match exists.
        4. Create a ``PaperSource`` tracking the provider.
        5. Link the paper to the investigation via ``InvestigationPaper``
           with the ranking and relevance score.

        Returns the list of paper UUIDs in rank order.
        """
        paper_ids: list[uuid.UUID] = []
        for rank, paper in enumerate(papers):
            db_paper = self._resolve_paper(paper)
            paper_ids.append(db_paper.id)
            self._create_source(db_paper.id, paper)
            self._repository.attach_to_investigation(
                InvestigationPaper(
                    investigation_id=investigation_id,
                    paper_id=db_paper.id,
                    rank=rank + 1,
                    relevance_score=paper.score,
                ),
            )
        self._session.commit()
        logger.info(
            "papers_persisted",
            investigation_id=str(investigation_id),
            count=len(papers),
        )
        return paper_ids

    def _resolve_paper(self, dto: PaperDTO) -> Paper:
        existing = None
        if dto.doi:
            existing = self._repository.get_by_doi(dto.doi)
        if existing is None:
            existing = self._repository.get_by_title(dto.title)
        if existing is not None:
            return existing
        return self._repository.create(
            Paper(
                title=dto.title,
                abstract=dto.abstract,
                authors=list(dto.authors) if dto.authors else [],
                doi=dto.doi,
                venue=dto.venue,
                year=dto.year,
                citation_count=dto.citation_count,
                url=dto.url,
            ),
        )

    def _create_source(self, paper_id: uuid.UUID, dto: PaperDTO) -> None:
        identifier = dto.doi or dto.url or dto.title
        self._repository.create_source(
            PaperSource(
                paper_id=paper_id,
                provider=dto.source,
                provider_identifier=identifier,
                raw_metadata={},
            ),
        )
