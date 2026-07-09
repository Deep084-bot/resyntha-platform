"""Collection REST API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.collection.api.schemas import (
    CollectionCreateRequest,
    CollectionPaperAddRequest,
    CollectionPaperResponse,
    CollectionResponse,
    CollectionUpdateRequest,
)
from app.modules.collection.repository.repository import CollectionRepository
from app.modules.collection.service.service import CollectionService

router = APIRouter(tags=["collections"])


def get_collection_service(db: Session = Depends(get_db)) -> CollectionService:
    return CollectionService(CollectionRepository(db))


# ── Collections ──────────────────────────────────────────────────


@router.get("/investigations/{investigation_id}/collections")
def list_collections(
    investigation_id: uuid.UUID,
    collection_service: CollectionService = Depends(get_collection_service),
) -> list[CollectionResponse]:
    collections = collection_service.list_collections(investigation_id)
    return [CollectionResponse.model_validate(c) for c in collections]


@router.post("/investigations/{investigation_id}/collections", status_code=201)
def create_collection(
    investigation_id: uuid.UUID,
    body: CollectionCreateRequest,
    collection_service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    collection = collection_service.create_collection(
        investigation_id=investigation_id,
        name=body.name,
        description=body.description,
    )
    return CollectionResponse.model_validate(collection)


@router.get("/collections/{collection_id}")
def get_collection(
    collection_id: uuid.UUID,
    collection_service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    collection = collection_service.get_collection(collection_id)
    return CollectionResponse.model_validate(collection)


@router.patch("/collections/{collection_id}")
def update_collection(
    collection_id: uuid.UUID,
    body: CollectionUpdateRequest,
    collection_service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    collection = collection_service.update_collection(
        collection_id=collection_id,
        name=body.name,
        description=body.description,
    )
    return CollectionResponse.model_validate(collection)


@router.delete("/collections/{collection_id}", status_code=204)
def delete_collection(
    collection_id: uuid.UUID,
    collection_service: CollectionService = Depends(get_collection_service),
) -> None:
    collection_service.delete_collection(collection_id)


# ── Collection Papers ────────────────────────────────────────────


@router.post("/collections/{collection_id}/papers", status_code=201)
def add_paper_to_collection(
    collection_id: uuid.UUID,
    body: CollectionPaperAddRequest,
    collection_service: CollectionService = Depends(get_collection_service),
) -> CollectionPaperResponse:
    link = collection_service.add_paper(collection_id, body.paper_id)
    return CollectionPaperResponse.model_validate(link)


@router.delete(
    "/collections/{collection_id}/papers/{paper_id}",
    status_code=204,
)
def remove_paper_from_collection(
    collection_id: uuid.UUID,
    paper_id: uuid.UUID,
    collection_service: CollectionService = Depends(get_collection_service),
) -> None:
    collection_service.remove_paper(collection_id, paper_id)
