"""Repository for the ``extracted_knowledge`` table."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.extraction.domain.models import ExtractedKnowledge


class ExtractionRepository:
    """Data-access layer for ``ExtractedKnowledge`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, knowledge: ExtractedKnowledge) -> ExtractedKnowledge:
        self._session.add(knowledge)
        self._session.flush()
        return knowledge

    def get_by_id(self, knowledge_id: uuid.UUID) -> ExtractedKnowledge | None:
        stmt = select(ExtractedKnowledge).where(
            ExtractedKnowledge.id == knowledge_id,
        )
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_investigation(
        self,
        investigation_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.investigation_id == investigation_id)
            .order_by(ExtractedKnowledge.created_at)
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def list_by_paper(
        self,
        paper_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.paper_id == paper_id)
            .order_by(ExtractedKnowledge.created_at.desc())
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def list_by_execution(
        self,
        execution_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.execution_id == execution_id)
            .order_by(ExtractedKnowledge.created_at)
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def delete(self, knowledge_id: uuid.UUID) -> bool:
        stmt = select(ExtractedKnowledge).where(
            ExtractedKnowledge.id == knowledge_id,
        )
        result = self._session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return False
        self._session.delete(obj)
        return True
