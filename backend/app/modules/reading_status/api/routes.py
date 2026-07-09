"""Paper reading status REST API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.reading_status.api.schemas import (
    ReadingStatusResponse,
    ReadingStatusSetRequest,
)
from app.modules.reading_status.repository.repository import ReadingStatusRepository
from app.modules.reading_status.service.service import ReadingStatusService

router = APIRouter(tags=["reading_status"])


def get_reading_status_service(db: Session = Depends(get_db)) -> ReadingStatusService:
    return ReadingStatusService(ReadingStatusRepository(db))


@router.get("/investigations/{investigation_id}/papers/{paper_id}/reading-status")
def get_reading_status(
    investigation_id: uuid.UUID,
    paper_id: uuid.UUID,
    reading_service: ReadingStatusService = Depends(get_reading_status_service),
) -> ReadingStatusResponse | None:
    status = reading_service.get_status(investigation_id, paper_id)
    if status is None:
        return None
    return ReadingStatusResponse.model_validate(status)


@router.put("/investigations/{investigation_id}/papers/{paper_id}/reading-status")
def set_reading_status(
    investigation_id: uuid.UUID,
    paper_id: uuid.UUID,
    body: ReadingStatusSetRequest,
    reading_service: ReadingStatusService = Depends(get_reading_status_service),
) -> ReadingStatusResponse:
    status = reading_service.set_status(investigation_id, paper_id, body.status)
    return ReadingStatusResponse.model_validate(status)
