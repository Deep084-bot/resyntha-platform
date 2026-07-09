"""Collection business logic."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status

from app.modules.collection.domain.models import Collection, CollectionPaper
from app.modules.collection.repository.repository import CollectionRepository


class CollectionService:
    """Business-logic layer for paper collections."""

    def __init__(self, repo: CollectionRepository) -> None:
        self._repo = repo

    # ── CRUD ───────────────────────────────────────────────────

    def create_collection(
        self,
        investigation_id: uuid.UUID,
        name: str,
        description: str | None = None,
    ) -> Collection:
        collection = Collection(
            investigation_id=investigation_id,
            name=name,
            description=description,
        )
        return self._repo.create(collection)

    def get_collection(self, collection_id: uuid.UUID) -> Collection:
        collection = self._repo.get_by_id(collection_id)
        if collection is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return collection

    def list_collections(self, investigation_id: uuid.UUID) -> Sequence[Collection]:
        return self._repo.list_by_investigation(investigation_id)

    def update_collection(
        self,
        collection_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Collection:
        self.get_collection(collection_id)
        kwargs: dict[str, object] = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if not kwargs:
            return self._repo.get_by_id(collection_id)  # type: ignore[return-value]
        result = self._repo.update(collection_id, **kwargs)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return result

    def delete_collection(self, collection_id: uuid.UUID) -> None:
        if not self._repo.delete(collection_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # ── Papers ─────────────────────────────────────────────────

    def add_paper(self, collection_id: uuid.UUID, paper_id: uuid.UUID) -> CollectionPaper:
        self.get_collection(collection_id)
        result = self._repo.add_paper(collection_id, paper_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return result

    def remove_paper(self, collection_id: uuid.UUID, paper_id: uuid.UUID) -> None:
        self.get_collection(collection_id)
        if not self._repo.remove_paper(collection_id, paper_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
