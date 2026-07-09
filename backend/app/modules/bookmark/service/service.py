"""Bookmark business logic."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status

from app.modules.bookmark.domain.models import Bookmark
from app.modules.bookmark.repository.repository import BookmarkRepository


class BookmarkService:
    """Business-logic layer for paper bookmarks."""

    def __init__(self, repo: BookmarkRepository) -> None:
        self._repo = repo

    def add_bookmark(self, investigation_id: uuid.UUID, paper_id: uuid.UUID, notes: str | None = None) -> Bookmark:
        existing = self._repo.get_by_paper(investigation_id, paper_id)
        if existing is not None:
            return existing
        bookmark = Bookmark(
            investigation_id=investigation_id,
            paper_id=paper_id,
            notes=notes,
        )
        return self._repo.create(bookmark)

    def list_bookmarks(self, investigation_id: uuid.UUID) -> Sequence[Bookmark]:
        return self._repo.list_by_investigation(investigation_id)

    def remove_bookmark(self, bookmark_id: uuid.UUID) -> None:
        if not self._repo.delete(bookmark_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
