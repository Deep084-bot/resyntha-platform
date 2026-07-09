"""Notes and highlights business logic."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status

from app.modules.notes.domain.models import Note, NoteLink
from app.modules.notes.repository.repository import NoteRepository


class NoteService:
    """Business-logic layer for notes and highlights."""

    def __init__(self, repo: NoteRepository) -> None:
        self._repo = repo

    # ── CRUD ───────────────────────────────────────────────────

    def create_note(
        self,
        investigation_id: uuid.UUID,
        title: str,
        content: str,
        tags: list[str] | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        source_context: str | None = None,
    ) -> Note:
        note = Note(
            investigation_id=investigation_id,
            title=title,
            content=content,
            tags=tags or [],
            source_type=source_type,
            source_id=source_id,
            source_context=source_context,
        )
        return self._repo.create(note)

    def get_note(self, note_id: uuid.UUID) -> Note:
        note = self._repo.get_by_id(note_id)
        if note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return note

    def list_notes(
        self,
        investigation_id: uuid.UUID,
        source_type: str | None = None,
    ) -> Sequence[Note]:
        return self._repo.list_by_investigation(investigation_id, source_type=source_type)

    def search_notes(self, investigation_id: uuid.UUID, query: str) -> Sequence[Note]:
        if not query.strip():
            return self._repo.list_by_investigation(investigation_id)
        return self._repo.search(investigation_id, query)

    def update_note(
        self,
        note_id: uuid.UUID,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> Note:
        kwargs: dict[str, object] = {}
        if title is not None:
            kwargs["title"] = title
        if content is not None:
            kwargs["content"] = content
        if tags is not None:
            kwargs["tags"] = tags
        if not kwargs:
            return self.get_note(note_id)
        result = self._repo.update(note_id, **kwargs)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return result

    def delete_note(self, note_id: uuid.UUID) -> None:
        if not self._repo.delete(note_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # ── Links ──────────────────────────────────────────────────

    def add_link(
        self,
        note_id: uuid.UUID,
        target_type: str,
        target_id: str,
        label: str | None = None,
    ) -> NoteLink:
        self.get_note(note_id)
        link = NoteLink(
            note_id=note_id,
            target_type=target_type,
            target_id=target_id,
            label=label,
        )
        return self._repo.create_link(link)

    def list_links(self, note_id: uuid.UUID) -> Sequence[NoteLink]:
        self.get_note(note_id)
        return self._repo.list_links(note_id)

    def delete_link(self, link_id: uuid.UUID) -> None:
        if not self._repo.delete_link(link_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
