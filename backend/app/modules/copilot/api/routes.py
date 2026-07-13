import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.llm.factory import ProviderFactory
from app.database.dependencies import get_db
from app.modules.copilot.schemas.request import ChatRequest
from app.modules.copilot.schemas.response import (
    ChatResponse,
    CopilotMessageResponse,
    StreamDone,
    StreamError,
    StreamToken,
)
from app.modules.copilot.service.service import CopilotService
from app.observability.logger import get_logger

router = APIRouter(prefix="/investigations/{investigation_id}/copilot", tags=["copilot"])
logger = get_logger(__name__)


def _get_service(db: Session = Depends(get_db)) -> CopilotService:
    provider = ProviderFactory.create(get_settings().LLM_PROVIDER)
    return CopilotService(db, llm_provider=provider)


@router.get("/messages", response_model=list[CopilotMessageResponse])
async def messages(
    investigation_id: uuid.UUID,
    service: CopilotService = Depends(_get_service),
) -> list[CopilotMessageResponse]:
    try:
        result = service.get_history(investigation_id)
        logger.info(
            "copilot_history",
            investigation_id=str(investigation_id),
            message_count=len(result),
        )
        return result
    except Exception as exc:
        logger.error("copilot_history_error", error=str(exc)[:500])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load copilot history",
        ) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(
    investigation_id: uuid.UUID,
    body: ChatRequest,
    service: CopilotService = Depends(_get_service),
) -> ChatResponse:
    try:
        result = await service.chat(investigation_id, body.question)
        logger.info(
            "copilot_chat",
            investigation_id=str(investigation_id),
            question_length=len(body.question),
        )
        return result
    except Exception as exc:
        logger.error("copilot_chat_error", error=str(exc)[:500])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        ) from exc


@router.post("/chat/stream")
async def chat_stream(
    investigation_id: uuid.UUID,
    body: ChatRequest,
    service: CopilotService = Depends(_get_service),
) -> StreamingResponse:
    async def event_generator():
        async for event in service.chat_stream(investigation_id, body.question):
            if isinstance(event, StreamToken):
                yield f"data: {event.model_dump_json()}\n\n"
            elif isinstance(event, StreamDone):
                yield f"data: {event.model_dump_json()}\n\n"
            elif isinstance(event, StreamError):
                yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
