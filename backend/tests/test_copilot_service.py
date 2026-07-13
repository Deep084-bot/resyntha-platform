from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.copilot.service.service import CopilotService


def _make_service() -> CopilotService:
    service = CopilotService(MagicMock())
    service._copilot_repo = MagicMock()
    return service


def test_get_history_returns_empty_list_when_conversation_missing() -> None:
    service = _make_service()
    investigation_id = uuid.uuid4()
    service._copilot_repo.get_conversation_by_investigation.return_value = None

    history = service.get_history(investigation_id)

    assert history == []
    service._copilot_repo.get_messages.assert_not_called()


def test_get_history_serializes_messages_with_metadata() -> None:
    service = _make_service()
    investigation_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    service._copilot_repo.get_conversation_by_investigation.return_value = SimpleNamespace(
        id=conversation_id,
    )
    service._copilot_repo.get_messages.return_value = [
        SimpleNamespace(
            id=uuid.uuid4(),
            role="user",
            content="Summarize the research.",
            _metadata={},
            created_at=datetime(2026, 7, 7, 10, 0, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            id=uuid.uuid4(),
            role="assistant",
            content="The research focuses on comparison tasks.",
            _metadata={
                "citations": [
                    {
                        "paper_title": "Paper One",
                        "paper_id": "paper-1",
                        "relevance": "Highly relevant",
                    }
                ],
                "suggested_questions": ["What methods dominate?"],
            },
            created_at=datetime(2026, 7, 7, 10, 0, 5, tzinfo=UTC),
        ),
    ]

    history = service.get_history(investigation_id)

    assert [message.role for message in history] == ["user", "assistant"]
    assert history[1].sources[0].paper_title == "Paper One"
    assert history[1].suggested_questions == ["What methods dominate?"]
    assert history[1].created_at == "2026-07-07T10:00:05+00:00"
