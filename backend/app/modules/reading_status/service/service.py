"""Paper reading status business logic."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.modules.reading_status.domain.models import PaperReadingStatus
from app.modules.reading_status.repository.repository import ReadingStatusRepository

VALID_STATUSES = {"unread", "reading", "completed", "skipped"}


class ReadingStatusService:
    """Business-logic layer for paper reading status."""

    def __init__(self, repo: ReadingStatusRepository) -> None:
        self._repo = repo

    def set_status(self, investigation_id: uuid.UUID, paper_id: uuid.UUID, status: str) -> PaperReadingStatus:
        if status not in VALID_STATUSES:
            status = "unread"
        return self._repo.upsert(investigation_id, paper_id, status)

    def get_status(self, investigation_id: uuid.UUID, paper_id: uuid.UUID) -> PaperReadingStatus | None:
        return self._repo.get(investigation_id, paper_id)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> Sequence[PaperReadingStatus]:
        return self._repo.list_by_investigation(investigation_id)
