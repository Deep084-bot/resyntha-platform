"""Notes and highlights API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NoteCreateRequest(BaseModel):
    title: str = ""
    content: str = ""
    tags: list[str] = []
    source_type: str | None = None
    source_id: str | None = None
    source_context: str | None = None


class NoteUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    title: str
    content: str
    tags: list[str]
    source_type: str | None
    source_id: str | None
    source_context: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteLinkCreateRequest(BaseModel):
    target_type: str
    target_id: str
    label: str | None = None


class NoteLinkResponse(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    target_type: str
    target_id: str
    label: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteSearchParams(BaseModel):
    q: str = ""


# ── Activity ──────────────────────────────────────────────────


class ActivityItem(BaseModel):
    type: str  # "note_created", "note_updated", "bookmark_added", "status_changed"
    description: str
    timestamp: datetime
    entity_id: str | None = None
    entity_type: str | None = None
