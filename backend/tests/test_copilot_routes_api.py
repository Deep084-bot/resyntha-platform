from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.v1 import v1_router
from app.modules.copilot.api.routes import _get_service
from app.modules.copilot.schemas.response import Citation, CopilotMessageResponse


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


def _override_service(app: FastAPI, service: MagicMock) -> None:
    app.dependency_overrides[_get_service] = lambda: service


def test_get_history_returns_empty_list_when_missing_conversation(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    service = MagicMock()
    service.get_history.return_value = []
    _override_service(test_app, service)

    investigation_id = uuid.uuid4()
    response = client.get(f"/investigations/{investigation_id}/copilot/messages")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_history_returns_ordered_messages(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    service = MagicMock()
    service.get_history.return_value = [
        CopilotMessageResponse(
            id="msg-1",
            role="user",
            content="What is the summary?",
            created_at="2026-07-07T10:00:00+00:00",
        ),
        CopilotMessageResponse(
            id="msg-2",
            role="assistant",
            content="Here is the summary.",
            sources=[
                Citation(
                    paper_title="Paper One",
                    paper_id="paper-1",
                    relevance="Highly relevant",
                )
            ],
            suggested_questions=["What methods dominate?"],
            created_at="2026-07-07T10:00:05+00:00",
        ),
    ]
    _override_service(test_app, service)

    investigation_id = uuid.uuid4()
    response = client.get(f"/investigations/{investigation_id}/copilot/messages")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert [message["id"] for message in body] == ["msg-1", "msg-2"]
    assert body[1]["sources"][0]["paper_title"] == "Paper One"
    assert body[1]["suggested_questions"] == ["What methods dominate?"]
