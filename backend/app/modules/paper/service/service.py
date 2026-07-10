"""Paper service."""

import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
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

        Uses batched DOI and title lookups to avoid N+1 queries.
        For each paper in the sequence:

        1. Look up by DOI (batched) — reuse if found.
        2. Fall back to exact title lookup (batched) — reuse if found.
        3. Create a new ``Paper`` record when neither match exists.
        4. Create a ``PaperSource`` tracking the provider.
        5. Link the paper to the investigation via ``InvestigationPaper``.

        Returns the list of paper UUIDs in rank order.
        """
        paper_ids: list[uuid.UUID] = []

        # Batch pre-load existing papers by DOI and title
        dois = [p.doi for p in papers if p.doi]
        doi_map = self._repository.batch_get_by_dois(dois) if dois else {}

        titles = [p.title for p in papers]
        title_map = self._repository.batch_get_by_titles(titles) if titles else {}

        try:
            for rank, paper in enumerate(papers):
                db_paper = doi_map.get(paper.doi or "") or title_map.get(paper.title)
                if db_paper is None:
                    db_paper = self._repository.create(
                        Paper(
                            title=paper.title,
                            abstract=paper.abstract,
                            authors=list(paper.authors) if paper.authors else [],
                            doi=paper.doi,
                            venue=paper.venue,
                            year=paper.year,
                            citation_count=paper.citation_count,
                            url=paper.url,
                        ),
                    )
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
        except IntegrityError:
            self._session.rollback()
            logger.error(
                "papers_persist_integrity_error",
                investigation_id=str(investigation_id),
            )
            raise

        logger.info(
            "papers_persisted",
            investigation_id=str(investigation_id),
            count=len(papers),
        )
        return paper_ids

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
