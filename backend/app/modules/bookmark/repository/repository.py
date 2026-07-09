"""Bookmark repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.bookmark.domain.models import Bookmark


class BookmarkRepository:
    """Data-access layer for ``Bookmark`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, bookmark: Bookmark) -> Bookmark:
        self._session.add(bookmark)
        self._session.flush()
        self._session.refresh(bookmark)
        return bookmark

    def get_by_id(self, bookmark_id: uuid.UUID) -> Bookmark | None:
        stmt = select(Bookmark).where(Bookmark.id == bookmark_id)
        return self._session.scalar(stmt)

    def get_by_paper(self, investigation_id: uuid.UUID, paper_id: uuid.UUID) -> Bookmark | None:
        stmt = (
            select(Bookmark)
            .where(Bookmark.investigation_id == investigation_id)
            .where(Bookmark.paper_id == paper_id)
        )
        return self._session.scalar(stmt)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[Bookmark]:
        stmt = (
            select(Bookmark)
            .where(Bookmark.investigation_id == investigation_id)
            .order_by(Bookmark.created_at.desc())
        )
        return self._session.scalars(stmt).all()

    def delete(self, bookmark_id: uuid.UUID) -> bool:
        stmt = delete(Bookmark).where(Bookmark.id == bookmark_id)
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount > 0
