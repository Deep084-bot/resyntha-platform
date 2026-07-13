"""Notes and highlights repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.notes.domain.models import Note, NoteLink


class NoteRepository:
    """Data-access layer for ``Note`` and ``NoteLink`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Notes ──────────────────────────────────────────────────

    def create(self, note: Note) -> Note:
        self._session.add(note)
        self._session.flush()
        self._session.refresh(note)
        return note

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        stmt = select(Note).where(Note.id == note_id)
        return self._session.scalar(stmt)

    def list_by_investigation(
        self,
        investigation_id: uuid.UUID,
        source_type: str | None = None,
    ) -> Sequence[Note]:
        stmt = (
            select(Note)
            .where(Note.investigation_id == investigation_id)
            .order_by(Note.updated_at.desc())
        )
        if source_type is not None:
            stmt = stmt.where(Note.source_type == source_type)
        return self._session.scalars(stmt).all()

    def search(
        self,
        investigation_id: uuid.UUID,
        query: str,
    ) -> Sequence[Note]:
        """Search notes by title or content using ILIKE."""
        pattern = f"%{query}%"
        stmt = (
            select(Note)
            .where(Note.investigation_id == investigation_id)
            .where(
                Note.title.ilike(pattern) | Note.content.ilike(pattern),
            )
            .order_by(Note.updated_at.desc())
        )
        return self._session.scalars(stmt).all()

    def update(self, note_id: uuid.UUID, **kwargs: object) -> Note | None:
        stmt = update(Note).where(Note.id == note_id).values(**kwargs).returning(Note)
        result = self._session.execute(stmt)
        self._session.flush()
        return result.scalar_one_or_none()

    def delete(self, note_id: uuid.UUID) -> bool:
        stmt = delete(Note).where(Note.id == note_id)
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount > 0

    # ── Note Links ─────────────────────────────────────────────

    def create_link(self, link: NoteLink) -> NoteLink:
        self._session.add(link)
        self._session.flush()
        self._session.refresh(link)
        return link

    def list_links(self, note_id: uuid.UUID) -> Sequence[NoteLink]:
        stmt = select(NoteLink).where(NoteLink.note_id == note_id).order_by(NoteLink.created_at)
        return self._session.scalars(stmt).all()

    def delete_link(self, link_id: uuid.UUID) -> bool:
        stmt = delete(NoteLink).where(NoteLink.id == link_id)
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount > 0
