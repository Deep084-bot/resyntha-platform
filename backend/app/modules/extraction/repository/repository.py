"""Repository for the ``extracted_knowledge`` table."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.extraction.domain.models import ExtractedKnowledge


class ExtractionRepository:
    """Data-access layer for ``ExtractedKnowledge`` records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, knowledge: ExtractedKnowledge) -> ExtractedKnowledge:
        self._session.add(knowledge)
        await self._session.flush()
        return knowledge

    async def get_by_id(self, knowledge_id: uuid.UUID) -> ExtractedKnowledge | None:
        stmt = select(ExtractedKnowledge).where(
            ExtractedKnowledge.id == knowledge_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_investigation(
        self,
        investigation_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.investigation_id == investigation_id)
            .order_by(ExtractedKnowledge.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_paper(
        self,
        paper_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.paper_id == paper_id)
            .order_by(ExtractedKnowledge.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_execution(
        self,
        execution_id: uuid.UUID,
    ) -> Sequence[ExtractedKnowledge]:
        stmt = (
            select(ExtractedKnowledge)
            .where(ExtractedKnowledge.execution_id == execution_id)
            .order_by(ExtractedKnowledge.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def delete(self, knowledge_id: uuid.UUID) -> bool:
        stmt = select(ExtractedKnowledge).where(
            ExtractedKnowledge.id == knowledge_id,
        )
        result = await self._session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return False
        await self._session.delete(obj)
        return True
