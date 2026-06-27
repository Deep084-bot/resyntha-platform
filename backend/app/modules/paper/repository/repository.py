"""Paper repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.paper.domain.models import InvestigationPaper, Paper, PaperSource


class PaperRepository:
    """Persistence gateway for ``Paper``, ``PaperSource``, and ``InvestigationPaper``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_doi(self, doi: str) -> Paper | None:
        """Return the paper matching *doi* or ``None``."""
        stmt = select(Paper).where(Paper.doi == doi)
        return self._session.scalar(stmt)

    def get_by_title(self, title: str) -> Paper | None:
        """Return the paper matching *title* exactly or ``None``."""
        stmt = select(Paper).where(Paper.title == title)
        return self._session.scalar(stmt)

    def create(self, paper: Paper) -> Paper:
        """Persist a new paper and return it with a generated id."""
        self._session.add(paper)
        self._session.flush()
        self._session.refresh(paper)
        return paper

    def create_source(self, source: PaperSource) -> PaperSource:
        """Persist a new paper source record."""
        self._session.add(source)
        self._session.flush()
        self._session.refresh(source)
        return source

    def attach_to_investigation(self, link: InvestigationPaper) -> InvestigationPaper:
        """Create a link between an investigation and a paper."""
        self._session.add(link)
        self._session.flush()
        self._session.refresh(link)
        return link

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[Paper]:
        """Return all papers attached to the given investigation, ordered by rank."""
        stmt = (
            select(Paper)
            .join(InvestigationPaper, InvestigationPaper.paper_id == Paper.id)
            .where(InvestigationPaper.investigation_id == investigation_id)
            .order_by(InvestigationPaper.rank.asc())
        )
        return self._session.scalars(stmt).all()
