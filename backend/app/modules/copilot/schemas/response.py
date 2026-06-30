from pydantic import BaseModel, Field


class Citation(BaseModel):
    paper_title: str = ""
    paper_id: str = ""
    relevance: str = ""


class CopilotMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[Citation] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    created_at: str = ""


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    suggested_questions: list[str] = Field(default_factory=list)
    message_id: str = ""
    conversation_id: str = ""
