"""Bookmark REST API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.bookmark.api.schemas import BookmarkCreateRequest, BookmarkResponse
from app.modules.bookmark.repository.repository import BookmarkRepository
from app.modules.bookmark.service.service import BookmarkService

router = APIRouter(tags=["bookmarks"])


def get_bookmark_service(db: Session = Depends(get_db)) -> BookmarkService:
    return BookmarkService(BookmarkRepository(db))


@router.get("/investigations/{investigation_id}/bookmarks")
def list_bookmarks(
    investigation_id: uuid.UUID,
    bookmark_service: BookmarkService = Depends(get_bookmark_service),
) -> list[BookmarkResponse]:
    bookmarks = bookmark_service.list_bookmarks(investigation_id)
    return [BookmarkResponse.model_validate(b) for b in bookmarks]


@router.post("/investigations/{investigation_id}/bookmarks", status_code=201)
def add_bookmark(
    investigation_id: uuid.UUID,
    body: BookmarkCreateRequest,
    bookmark_service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkResponse:
    bookmark = bookmark_service.add_bookmark(
        investigation_id=investigation_id,
        paper_id=body.paper_id,
        notes=body.notes,
    )
    return BookmarkResponse.model_validate(bookmark)


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
def remove_bookmark(
    bookmark_id: uuid.UUID,
    bookmark_service: BookmarkService = Depends(get_bookmark_service),
) -> None:
    bookmark_service.remove_bookmark(bookmark_id)
