import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.copilot.domain.models import CopilotConversation, CopilotMessage


class CopilotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_conversation_by_investigation(
        self, investigation_id: uuid.UUID
    ) -> CopilotConversation | None:
        return (
            self._session.query(CopilotConversation)
            .filter(CopilotConversation.investigation_id == investigation_id)
            .first()
        )

    def create_conversation(self, investigation_id: uuid.UUID) -> CopilotConversation:
        conversation = CopilotConversation(investigation_id=investigation_id)
        self._session.add(conversation)
        self._session.flush()
        return conversation

    def get_messages(self, conversation_id: uuid.UUID) -> Sequence[CopilotMessage]:
        return (
            self._session.query(CopilotMessage)
            .filter(CopilotMessage.conversation_id == conversation_id)
            .order_by(CopilotMessage.created_at)
            .all()
        )

    def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> CopilotMessage:
        message = CopilotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            _metadata=metadata or {},
        )
        self._session.add(message)
        self._session.flush()
        return message
