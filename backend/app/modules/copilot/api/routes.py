import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.copilot.schemas.request import ChatRequest
from app.modules.copilot.schemas.response import ChatResponse
from app.modules.copilot.service.service import CopilotService
from app.observability.logger import get_logger

router = APIRouter(prefix="/investigations/{investigation_id}/copilot", tags=["copilot"])
logger = get_logger(__name__)


def _get_service(db: Session = Depends(get_db)) -> CopilotService:
    return CopilotService(db)


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
