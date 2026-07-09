"""Notes and highlights REST API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.notes.api.schemas import (
    NoteCreateRequest,
    NoteLinkCreateRequest,
    NoteLinkResponse,
    NoteResponse,
    NoteUpdateRequest,
)
from app.modules.notes.repository.repository import NoteRepository
from app.modules.notes.service.service import NoteService

router = APIRouter(tags=["notes"])


def get_note_service(db: Session = Depends(get_db)) -> NoteService:
    return NoteService(NoteRepository(db))


# ── Notes ──────────────────────────────────────────────────────


@router.get("/investigations/{investigation_id}/notes")
def list_notes(
    investigation_id: uuid.UUID,
    source_type: str | None = Query(None),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteResponse]:
    notes = note_service.list_notes(investigation_id, source_type=source_type)
    return [NoteResponse.model_validate(n) for n in notes]


@router.post("/investigations/{investigation_id}/notes", status_code=201)
def create_note(
    investigation_id: uuid.UUID,
    body: NoteCreateRequest,
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    note = note_service.create_note(
        investigation_id=investigation_id,
        title=body.title,
        content=body.content,
        tags=body.tags,
        source_type=body.source_type,
        source_id=body.source_id,
        source_context=body.source_context,
    )
    return NoteResponse.model_validate(note)


@router.get("/investigations/{investigation_id}/notes/search")
def search_notes(
    investigation_id: uuid.UUID,
    q: str = Query(""),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteResponse]:
    notes = note_service.search_notes(investigation_id, q)
    return [NoteResponse.model_validate(n) for n in notes]


@router.get("/notes/{note_id}")
def get_note(
    note_id: uuid.UUID,
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    note = note_service.get_note(note_id)
    return NoteResponse.model_validate(note)


@router.patch("/notes/{note_id}")
def update_note(
    note_id: uuid.UUID,
    body: NoteUpdateRequest,
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    note = note_service.update_note(
        note_id=note_id,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return NoteResponse.model_validate(note)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: uuid.UUID,
    note_service: NoteService = Depends(get_note_service),
) -> None:
    note_service.delete_note(note_id)


# ── Note Links ─────────────────────────────────────────────────


@router.get("/notes/{note_id}/links")
def list_links(
    note_id: uuid.UUID,
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteLinkResponse]:
    links = note_service.list_links(note_id)
    return [NoteLinkResponse.model_validate(l) for l in links]


@router.post("/notes/{note_id}/links", status_code=201)
def add_link(
    note_id: uuid.UUID,
    body: NoteLinkCreateRequest,
    note_service: NoteService = Depends(get_note_service),
) -> NoteLinkResponse:
    link = note_service.add_link(
        note_id=note_id,
        target_type=body.target_type,
        target_id=body.target_id,
        label=body.label,
    )
    return NoteLinkResponse.model_validate(link)


@router.delete("/links/{link_id}", status_code=204)
def delete_link(
    link_id: uuid.UUID,
    note_service: NoteService = Depends(get_note_service),
) -> None:
    note_service.delete_link(link_id)
