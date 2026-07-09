"""Collection API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class CollectionCreateRequest(BaseModel):
    name: str
    description: str | None = None


class CollectionUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class CollectionResponse(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CollectionPaperAddRequest(BaseModel):
    paper_id: uuid.UUID


class CollectionPaperResponse(BaseModel):
    collection_id: uuid.UUID
    paper_id: uuid.UUID
    added_at: datetime

    model_config = {"from_attributes": True}
