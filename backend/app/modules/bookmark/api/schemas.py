"""Bookmark API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class BookmarkCreateRequest(BaseModel):
    paper_id: uuid.UUID
    notes: str | None = None


class BookmarkResponse(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    paper_id: uuid.UUID
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
