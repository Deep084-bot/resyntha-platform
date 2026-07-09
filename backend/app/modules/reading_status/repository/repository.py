"""Paper reading status repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reading_status.domain.models import PaperReadingStatus


class ReadingStatusRepository:
    """Data-access layer for ``PaperReadingStatus`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, investigation_id: uuid.UUID, paper_id: uuid.UUID) -> PaperReadingStatus | None:
        stmt = (
            select(PaperReadingStatus)
            .where(PaperReadingStatus.investigation_id == investigation_id)
            .where(PaperReadingStatus.paper_id == paper_id)
        )
        return self._session.scalar(stmt)

    def upsert(
        self,
        investigation_id: uuid.UUID,
        paper_id: uuid.UUID,
        status: str,
    ) -> PaperReadingStatus:
        existing = self.get(investigation_id, paper_id)
        if existing is not None:
            existing.status = status
            self._session.flush()
            self._session.refresh(existing)
            return existing
        record = PaperReadingStatus(
            investigation_id=investigation_id,
            paper_id=paper_id,
            status=status,
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return record

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[PaperReadingStatus]:
        stmt = (
            select(PaperReadingStatus)
            .where(PaperReadingStatus.investigation_id == investigation_id)
        )
        return self._session.scalars(stmt).all()

    def list_by_status(self, investigation_id: uuid.UUID, status: str) -> Sequence[PaperReadingStatus]:
        stmt = (
            select(PaperReadingStatus)
            .where(PaperReadingStatus.investigation_id == investigation_id)
            .where(PaperReadingStatus.status == status)
        )
        return self._session.scalars(stmt).all()
