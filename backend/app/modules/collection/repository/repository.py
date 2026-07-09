"""Collection repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.collection.domain.models import Collection, CollectionPaper


class CollectionRepository:
    """Data-access layer for ``Collection`` and ``CollectionPaper`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Collections ────────────────────────────────────────────

    def create(self, collection: Collection) -> Collection:
        self._session.add(collection)
        self._session.flush()
        self._session.refresh(collection)
        return collection

    def get_by_id(self, collection_id: uuid.UUID) -> Collection | None:
        stmt = select(Collection).where(Collection.id == collection_id)
        return self._session.scalar(stmt)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[Collection]:
        stmt = (
            select(Collection)
            .where(Collection.investigation_id == investigation_id)
            .order_by(Collection.name)
        )
        return self._session.scalars(stmt).all()

    def update(self, collection_id: uuid.UUID, **kwargs: object) -> Collection | None:
        stmt = (
            update(Collection)
            .where(Collection.id == collection_id)
            .values(**kwargs)
            .returning(Collection)
        )
        result = self._session.execute(stmt)
        self._session.flush()
        return result.scalar_one_or_none()

    def delete(self, collection_id: uuid.UUID) -> bool:
        stmt = delete(Collection).where(Collection.id == collection_id)
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount > 0

    # ── Collection Papers ──────────────────────────────────────

    def add_paper(self, collection_id: uuid.UUID, paper_id: uuid.UUID) -> CollectionPaper | None:
        existing = self._session.get(CollectionPaper, (collection_id, paper_id))
        if existing is not None:
            return existing
        link = CollectionPaper(collection_id=collection_id, paper_id=paper_id)
        self._session.add(link)
        self._session.flush()
        return link

    def remove_paper(self, collection_id: uuid.UUID, paper_id: uuid.UUID) -> bool:
        link = self._session.get(CollectionPaper, (collection_id, paper_id))
        if link is None:
            return False
        self._session.delete(link)
        self._session.flush()
        return True

    def list_papers(self, collection_id: uuid.UUID) -> Sequence[CollectionPaper]:
        stmt = (
            select(CollectionPaper)
            .where(CollectionPaper.collection_id == collection_id)
            .order_by(CollectionPaper.added_at)
        )
        return self._session.scalars(stmt).all()
